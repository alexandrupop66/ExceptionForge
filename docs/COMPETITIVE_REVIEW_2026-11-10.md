# ExceptionForge — analiză comparativă după Vultr Agent Rush 2026

**Data:** 10/11/2026 · **Status:** submitted, public, fără premiu pe podium  
**Baza codului depus:** [stage2/security-gate-2026-11-08](https://github.com/alexandrupop66/ExceptionForge/tree/stage2/security-gate-2026-11-08), commit \`5408002a7ccf0549dd3ed3da9419dbf6425818b1\`.  
**Raport complet, DOCX editabil și Markdown:** [arhiva privată Google Drive](https://drive.google.com/drive/folders/1fJfnTK0YT27ZBVT8NYpKCa0-6OuhtiIQ) (denumire \`ExceptionForge_Analiza_Comparativa_Castigatori_10-11-2026.docx\`).  
**Documentul de față:** publicat pe branchul *archive/postmortem-2026-11-10*, fără modificări în codul sau branchul trimis juriului.

## 1. Bilanțul tehnic verificabil

- Aplicație publică pe Vultr VM: http://45.77.230.86/. Evaluarea externă anterioară a confirmat workflowul **determinist** pe 32 facturi sintetice, 15 excepții și citări la rânduri CSV.
- Separat, execuție **reală** pe VM prin Vultr Serverless Inference (\`deepseek-v4.1-flash-1017\`), Python generat și Docker: 32 facturi, 18 constatări, 9,85 s, o încercare.
- Probă reală de blocare a rețelei Docker, răspuns \`[Errno 101] Network unreachable\`. Demonstrează restricția testată, nu certificarea de securitate a întregului sistem.
- Jurnal de server: 55 teste trecute și un avertisment după patch; **nu** teste reexecutate după publicarea acestui commit GitHub.
- Codul de pe VM versus codul din GitHub: paritate exactă byte-for-byte **neconfirmată**.
- Video-ul final: 72,92 s, Full HD, subtitrat, fără voice-over. Materialele privind AI și containment sunt carduri rezumative, nu filmări live ale execuției.
- Endpointurile AI/Docker privilegiate nu sunt accesibile publicului anonim; proiectul nu poate efectua plăți.

## 2. Clasamentul oficial

Sursă primară: anunțul organizatorilor prin e-mail „Vultr: Agent Rush — Winners Announcement”, **10/11/2026, 00:45 GMT**.

| Loc | Proiect | Echipă | Premiu cash | Credite Vultr | Descriere oficială |
|---|---|---|---:|---:|---|
| 1 | **Airlock — Run the PR before you trust it** | **V3N** | $5,000 | $3,000 | Testează pull request-uri în sandboxuri izolate, detectează dependențe suspecte, acces la secrete și activitate de rețea ascunsă, produce verdicte bazate pe dovezi. |
| 2 | **Follow the Money: Agents that trace every payment** | **Fire Exit** | $3,000 | $1,000 | Șapte agenți urmăresc tranzacții și relații suspecte între furnizori, integrând facturi, chitanțe și tranzacții; deciziile rămân la oameni. |
| 3 | **Errand: your agent never sees the password** | **Errand** | $1,000 | $1,000 | Agent pentru comparația ofertelor și pregătirea comenzilor fără acces la parole; finalizarea achizițiilor cere aprobarea umană. |

**Atenție:** proiectul „Airlock (Blast Radius Zero)” al echipei *Airlock BR0*, prezent de asemenea pe platformă, **nu este** câștigătorul V3N. Nu am atribuit câștigătorilor metrici de testare sau funcții din proiecte omonime.

## 3. Comparație la rubricile oficiale

Organizatorii au evaluat **Application of Technology, Presentation, Business Value, Originality**; punctajele individuale nu au fost comunicate.

### Application of Technology
ExceptionForge a utilizat AI real și Docker real, dar demonstrația publică era doar deterministă. Airlock oferă, conform anunțului, un control direct asupra PR-urilor în sandbox. Follow the Money comunică o orchestrare cu șapte agenți, iar Errand un control al accesului la credențiale. Fără codul și jurnalele câștigătorilor nu se pot atribui performanțe tehnice comparative.

### Presentation
ExceptionForge a avut un video scurt și subtitrat, însă fără voice-over și fără filmarea unui test live de containment. Cele trei proiecte premiate transmit mecanismul principal într-o propoziție. Nu există audit comparativ al interfețelor sau al materialelor video ale câștigătorilor.

### Business Value
ExceptionForge este util pentru verificatorii care reconciliază exporturi CSV eterogene. Totuși, după identificarea excepțiilor, demo-ul nu arată închiderea întregului workflow. Airlock susține integrarea în review-ul de PR; Follow the Money extinde ancheta financiară la relații între entități; Errand pregătește achiziția sub aprobarea omului.

### Originality
Diferentiatorul ExceptionForge este generarea unei analize pentru scheme necunoscute plus citarea rândurilor sursă. Lipsesc benchmarkul live vs. baseline și validarea completă a celor 18 constatări AI. Descrierile oficiale ale câștigătorilor arată diferențiatori ușor de demonstrat, dar originalitatea lor absolută nu a fost auditată.

## 4. Constatări, nu explicații atribuite juriului

1. **Încredere mare:** flux public determinist, flux AI real separat. Demonstrația agentică nu era reproductibilă pentru un jurat anonim.
2. **Încredere mare:** momentul de izolare a fost comunicat prin carduri; brief-ul cerea să fie arătat în video.
3. **Încredere mare:** 18 constatări AI nu echivalează cu detectarea corectă a celor 15 etichete; lipsesc TP/FP/FN, precizie, recall și benchmark contra baseline.
4. **Încredere mare:** branchul GitHub implicit \`main\` conține versiunea anterioară; branchul corect a fost legat la înscriere, dar poate fi mai puțin intuitiv.
5. **Încredere medie:** video fără voce și cu interfață bazată pe demonstrația locală a redus posibil efectul narativ.
6. **Încredere medie:** nu a fost evident un flux de rezolvare până la confirmarea umană a constatării.

**Niciuna dintre acestea nu este motiv oficial comunicat de juriu.** Fără fișa de jurizare nu putem explica exact ordinea.

## 5. Recomandări pentru reutilizare, nu builduri aprobate

**Verdict: CONDITIONAL GO.** Păstrăm nucleul de proveniență, gardurile financiare și istoricul Git; construim doar dacă o viitoare competiție permite reutilizarea și după aprobare expresă.

**P0:**
- Demo de 20–30 secunde cu AI real: import → generare de cod → Docker → rezultat verificabil și citare.
- Filmare efectivă a unui atac refuzat de sandbox, nu doar un slide cu rezultat.
- Benchmark pe fixture sintetic și scheme noi: precizie, recall, F1, latență, cost, fals-pozitive, comparație cu regulile fixe; etichetele nu sunt transmise modelului.
- Commit/VM/documentație în paritate verificabilă; teste finale pe versiunea depusă.
- Video dinamic cu narațiune profesională ori subtitrări suficient de lizibile; fără dependență de promoții TTS.

**P1:** pași \`verify / escalate / archive\`, testare adversarială suplimentară, observabilitate, HTTPS și limite de cheltuieli pentru un eventual demo public viitor.

**Criteriu STOP:** dacă nu se poate demonstra în sub 30 secunde mecanismul agentic real, cu dovadă de izolare, nu adăugăm funcții decorative și nu afirmăm că proiectul este competitiv.

## 6. Arhiva și responsabilități

- **Google Drive:** ZIP-urile Stage 1/Stage 2/Local Demo/Security Gate, handofful original, finalul submission (MP4/PDF/PPTX/copertă), manifestul SHA-256, confirmarea de înscriere și raportul comparativ complet.
- **GitHub:** sursa, README, MIT, teste, istoricul vechi și backup; acest postmortem pe **branch separat**, nu peste versiunea depusă.
- **Neconfirmat:** backup independent al întregului VM și identitatea byte-for-byte a codului executat față de Github. Nu sunt arhivate public chei sau alte credențiale.
- **Cost:** utilizatorul nu a primit creditul promoțional Vultr $200. Instanța poate continua să factureze; acest document nu autorizează oprirea ori ștergerea ei.

### Surse

1. E-mail oficial lablab.ai, „Vultr: Agent Rush — Winners Announcement”, 10/11/2026, 00:45 GMT (inbox personal; sursă pentru clasament și descrieri).
2. [Vultr Community — brief, livrabile și criterii](https://community.vultr.com/e/vultr-agent-rush-hackathon).
3. [lablab.ai — competiția și provocările](https://lablab.build/ai-hackathons/vultr-hackathon).
4. [ExceptionForge — codul depus](https://github.com/alexandrupop66/ExceptionForge/tree/stage2/security-gate-2026-11-08).
5. Arhivele de handoff și submission datate 08/11/2026, [Drive folder](https://drive.google.com/drive/folders/1fJfnTK0YT27ZBVT8NYpKCa0-6OuhtiIQ).

*Metodă: fapte verificate despre ExceptionForge; descrierile câștigătorilor provenite din comunicatul organizatorilor; orice explicație a rezultatului este explicit inferență. Niciun audit independent al codului câștigătorilor și niciun scor de jurizare nu sunt disponibile.*