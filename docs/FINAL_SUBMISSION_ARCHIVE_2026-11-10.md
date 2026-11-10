# ExceptionForge — arhiva depunerii Vultr Agent Rush 2026 (10/11/2026)

**Notă:** documentație adăugată după terminarea competiției, într-un branch de arhivă. Nu modifică versiunea trimisă juriului, codul, demo-ul sau serverul.

## Repo și commituri

- [Repository public](https://github.com/alexandrupop66/ExceptionForge)
- **Versiunea depusă:** [\`stage2/security-gate-2026-11-08\`](https://github.com/alexandrupop66/ExceptionForge/tree/stage2/security-gate-2026-11-08), HEAD \`5408002a7ccf0549dd3ed3da9419dbf6425818b1\`.
- Backup pre-sincronizare: \`archive/exceptionforge-pre-submission-sync-2026-11-08\`, HEAD \`5690dc61cf9129269bcd60cc0ad09da1953073af\`.
- \`main\` este încă branchul implicit cu Stage 1; nu a fost rescris ori mutat.
- Paritatea între fișierul \`app/inference.py\` de pe VM și sursa GitHub nu a fost verificată byte-for-byte.

## Păstrare în Google Drive

[Folderul privat de handoff și arhivare](https://drive.google.com/drive/folders/1fJfnTK0YT27ZBVT8NYpKCa0-6OuhtiIQ)

- [Final Submission ZIP](https://drive.google.com/file/d/1YicZI0oPqB5pqhZoukfvytPygFcoPgMW/view): MP4 original subtitrat, PDF de șase slide-uri, PPTX editabil, coperta PNG, descrierea pentru formular, checklist și subtitrări.
- [Handoff ZIP](https://drive.google.com/file/d/1Hrp94CMalmV0c5SAU4qJAtwwZ-ljNlZ_/view): originale video, proba de inferență și containment, checkpoint, subtitrări și alte materiale.
- [Analiza comparativă DOCX](https://drive.google.com/file/d/1b3cYTAEehiICKAG0ZmzehxBn3kqmMuXZ/view) și [versiunea Markdown](https://drive.google.com/file/d/1r7H-9jBicLJp8ETvpowq22jgg3G6Pypm/view).
- [Manifestul SHA-256](https://drive.google.com/file/d/1KUaKlowDkVZCSwedsc9O8PwmQg-1JAUh/view).
- [Captura de confirmare a înscrierii](https://drive.google.com/file/d/1iPcOW4Quin3j22ogLdwCXEdTF6Q8Ru8i/view).
- Drive root păstrează ZIP-urile anterioare Stage 1, Stage 2, Local Demo și Security Gate. Niciun fișier existent nu a fost suprascris.

## SHA-256 fișiere depuse (calculate local, 10/11/2026)

| Fișier | SHA-256 |
|---|---|
| \`ExceptionForge_Submission_Ready_2026-11-08.zip\` | \`ec6958b2acb1bcc959633c73756ea748ac6e8a5b620fe4da90fdf6473e49b45d\` |
| \`ExceptionForge_Handoff_2026-11-08(1).zip\` | \`33e87a21755e363918625780c7f866a6ea5ca7de57873a956dd6fbc037c41b9f\` |
| \`ExceptionForge_Subtitled_1080p.mp4\` | \`333d196b53869ae7a4214c7efa4b07063775118c84a54c0d0a6a1871f21d9edf\` |
| \`ExceptionForge_Submission_Presentation.pdf\` | \`f361c827ff985b279d79d023448bc239bcb49cd7f3f46613198c4a2c93fb92b9\` |
| \`ExceptionForge_Submission_Presentation.pptx\` | \`791b04c39e68556cda80c8b174ea31102f564ce9d8a889883d1c2058dca88fa7\` |
| \`ExceptionForge_Cover_1920x1080.png\` | \`f869a647c7a440a9f765af5e506f72b5f035857662a0cd7a0382c57884e1d4ce\` |

## Delimitări și securitate

1. Fișierul cu voice-over robotic este un export respins, **nu** materialul depus juriului. Versiunea utilizată la înscriere avea 72,92 s, 1080p, subtitrări și fără voce.
2. Publicul putea testa **regulile deterministe** pe date sintetice. Execuția AI reală Vultr și testul Docker au fost rulate separat și documentate fără a pretinde că erau înregistrări live în clip.
3. Nu se publică tokenuri, API keys, variabile de mediu sau configurații sensibile în GitHub ori Drive.
4. Lipsesc verificarea backupului complet al VM, snapshot independent de configurare Nginx/Docker și demonstrația că versiunea live este identică cu GitHub. Arhivele păstrează codul și materialele cunoscute, **nu** garantează reconstruirea 1:1 a VM.
5. Serverul Vultr nu a fost oprit sau modificat de această operațiune; nu s-au inițiat cheltuieli sau achiziții.
6. [Analiza comparativă](COMPETITIVE_REVIEW_2026-11-10.md) este o retrospectivă, nu feedback oficial al juriului.
