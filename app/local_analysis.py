"""Auditable, deterministic local demonstration of procurement reconciliation.

This is a limited, rule-based baseline for the documented synthetic CSV schema.
No model calls, Docker execution, outbound requests, approval actions or data writes.
It MUST NOT be presented as Vultr inference or autonomous agent behaviour.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re

from .sandbox import SandboxError

HEADERS = {
    "purchase_orders.csv": {"PO Code", "Supplier Legal", "Product SKU", "Qty Placed", "Agreed GBP", "Pack Qty"},
    "goods_receipts.csv": {"Document", "Purchase Ref", "Cases In", "Units Per Case"},
    "invoices.csv": {"Bill Number", "Order Memo", "Payee Trading As", "Stock ID", "Billed Units", "Billed Unit", "Net GBP", "Price GBP", "Supplier Note"},
}


def _load(path: Path) -> list[tuple[int, dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = HEADERS[path.name] - set(reader.fieldnames or [])
        if missing:
            # Explicit non-support is preferable to inventing column matches.
            raise SandboxError(f"Local rules require documented CSV columns in {path.name}: {', '.join(sorted(missing))}. Use the Vultr AI mode for other layouts.")
        return [(reader.line_num, row) for row in reader]


def _decimal(row: dict[str, str], key: str, source: str, line: int) -> Decimal:
    try:
        value = Decimal(row[key].strip())
        if not value.is_finite():
            raise InvalidOperation
        return value
    except (KeyError, ValueError, InvalidOperation, AttributeError) as exc:
        raise SandboxError(f"Invalid numeric value for {source}:{line}, column {key}") from exc


def _identity(name: str) -> str:
    # Tolerate the Ltd/Limited aliases in the SYNTHETIC test data, not a legal-entity guarantee.
    tokens = re.findall(r"[a-z0-9]+", name.casefold())
    return " ".join(x for x in tokens if x not in {"ltd", "limited", "plc", "inc", "company", "co"})


def analyse_local(data_dir: Path) -> dict:
    purchase = _load(data_dir / "purchase_orders.csv")
    receipts = _load(data_dir / "goods_receipts.csv")
    invoices = _load(data_dir / "invoices.csv")
    po_by_ref = {row["PO Code"].strip(): (line, row) for line, row in purchase}
    receipts_by_ref: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    for line, row in receipts:
        receipts_by_ref[row["Purchase Ref"].strip()].append((line, row))
    id_counts = Counter(row["Bill Number"].strip() for _, row in invoices)
    grouped: dict[str, list[tuple[int, dict, Decimal]]] = defaultdict(list)
    findings: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def emit(line: int, row: dict, kind: str, reason: str, evidence: list[str]) -> None:
        ref = row["Bill Number"].strip()
        if (ref, kind) in seen:
            return
        seen.add((ref, kind))
        clean = list(dict.fromkeys([f"invoices.csv:{line}", *evidence]))
        findings.append({"invoice_ref": ref, "kind": kind, "reason": reason, "evidence": clean[:12]})

    for line, row in invoices:
        ref = row["Bill Number"].strip()
        if not ref:
            raise SandboxError(f"Missing invoice identifier at invoices.csv:{line}")
        po_refs = list(dict.fromkeys(re.findall(r"PO-[A-Za-z0-9-]+", row["Order Memo"])))
        links = [(po, po_by_ref[po]) for po in po_refs if po in po_by_ref]
        evidence_po = [f"purchase_orders.csv:{p[0]}" for _, p in links]
        evidence_gr = [f"goods_receipts.csv:{l}" for po, _ in links for l, _ in receipts_by_ref.get(po, [])]
        billed = _decimal(row, "Billed Units", "invoices.csv", line)
        billed_price = _decimal(row, "Price GBP", "invoices.csv", line)
        billed_net = _decimal(row, "Net GBP", "invoices.csv", line)

        # Credit notes need an original invoice reference, not merely a purchase order.
        if ref.startswith("CRN-") or billed < 0:
            note = row["Supplier Note"]
            if not re.search(r"INV-[A-Za-z0-9-]+", note):
                emit(line, row, "unlinked_credit_note", "Credit note has no original invoice reference; cannot safely apply it to a prior bill.", evidence_po)
            continue

        if id_counts[ref] > 1:
            related = [f"invoices.csv:{n}" for n, other in invoices if other["Bill Number"].strip() == ref]
            emit(line, row, "duplicate_invoice_number", "Invoice identifier appears multiple times in the supplied file; review possible duplicate submission.", related)

        if not po_refs:
            emit(line, row, "missing_purchase_reference", "Invoice has no purchase-order reference, preventing reliable reconciliation.", [])
            continue
        if len(links) != len(po_refs):
            emit(line, row, "missing_purchase_reference", "Referenced purchase order was not found in the supplied order export.", evidence_po)
            continue

        payee = _identity(row["Payee Trading As"])
        matching_suppliers = {_identity(po[1]["Supplier Legal"]) for _, po in links}
        if "/" in row["Payee Trading As"] or " or " in row["Payee Trading As"].casefold():
            emit(line, row, "ambiguous_supplier_identity", "Trading name is ambiguous and cannot be tied to a single legal supplier.", evidence_po)
        elif payee not in matching_suppliers:
            kind = "supplier_identity_mismatch"
            emit(line, row, kind, "Invoice payee does not match the purchase-order legal supplier after basic Ltd/Limited normalisation; verify identity manually.", evidence_po)

        skus = {po[1]["Product SKU"].strip() for _, po in links}
        if row["Stock ID"].strip() not in skus:
            emit(line, row, "product_code_conflict", "Invoiced product code is absent from the linked purchase orders.", evidence_po)

        if len(links) == 1:
            po_ref, po = links[0]
            po_line, po_row = po
            agreed = _decimal(po_row, "Agreed GBP", "purchase_orders.csv", po_line)
            if billed_price != agreed:
                emit(line, row, "price_variance", f"Invoice unit price £{billed_price} differs from agreed £{agreed}.", evidence_po)
        unit = row["Billed Unit"].strip().casefold()
        if unit in {"cartons", "carton", "cases", "case", "packs", "pack"}:
            if len(links) != 1:
                raise SandboxError(f"Cannot normalise pack units across multiple orders at invoices.csv:{line}")
            po_line, po_row = links[0][1]
            physical = billed * _decimal(po_row, "Pack Qty", "purchase_orders.csv", po_line)
        elif unit in {"pieces", "piece", "units", "unit", "each"}:
            physical = billed
        else:
            raise SandboxError(f"Unsupported billed unit at invoices.csv:{line}: {row['Billed Unit']}")

        if billed_net != physical * billed_price:
            emit(line, row, "arithmetic_mismatch", f"Invoice net £{billed_net} does not equal normalised quantity × unit price (£{physical * billed_price}).", evidence_po)
        if len(links) == 1 and id_counts[ref] == 1:
            grouped[po_refs[0]].append((line, row, physical))
        elif len(links) > 1:
            ordered = sum((_decimal(po, "Qty Placed", "purchase_orders.csv", pn) for _, (pn, po) in links), Decimal(0))
            received = sum((_decimal(rec, "Cases In", "goods_receipts.csv", rn) * _decimal(rec, "Units Per Case", "goods_receipts.csv", rn) for pref, _ in links for rn, rec in receipts_by_ref.get(pref, [])), Decimal(0))
            if physical > min(ordered, received):
                emit(line, row, "consolidated_invoice_exceeds_receipt", f"Consolidated invoice bills {physical} pieces against {ordered} ordered and {received} received across {len(links)} orders.", evidence_po + evidence_gr)

    for po_ref, group in grouped.items():
        po_line, po_row = po_by_ref[po_ref]
        ordered = _decimal(po_row, "Qty Placed", "purchase_orders.csv", po_line)
        total_received = sum((_decimal(rec, "Cases In", "goods_receipts.csv", ln) * _decimal(rec, "Units Per Case", "goods_receipts.csv", ln) for ln, rec in receipts_by_ref.get(po_ref, [])), Decimal(0))
        total_billed = sum((quantity for _, _, quantity in group), Decimal(0))
        if total_billed <= min(ordered, total_received):
            continue
        # Attribute cumulative split overbilling to the first entry that crosses the limit.
        running = Decimal(0)
        for line, row, physical in group:
            running += physical
            if running <= min(ordered, total_received):
                continue
            kind = ("split_invoice_total_exceeds_receipt" if len(group) > 1 else
                    "package_unit_overcharge" if row["Billed Unit"].casefold() in {"cartons", "carton", "cases", "case", "packs", "pack"} else
                    "over_billed_quantity" if total_billed > ordered else "invoice_exceeds_goods_received")
            ev = [f"purchase_orders.csv:{po_line}"] + [f"goods_receipts.csv:{ln}" for ln, _ in receipts_by_ref.get(po_ref, [])]
            if len(group) > 1:
                ev.extend(f"invoices.csv:{ln}" for ln, _, _ in group)
            emit(line, row, kind, f"{po_ref}: {total_billed} pieces billed, {ordered} ordered, {total_received} received (after package conversion).", ev)
            break
    # Security note findings are independently appended by _check_evidence in main.py.
    return {"findings": findings, "analysed_invoices": len(invoices)}
