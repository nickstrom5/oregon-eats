# Public records request to send (draft for Nick; nothing has been sent)

Nick's call 2026-10-24: draft a request to the Oregon Health Authority for a statewide restaurant inspection extract; Nick sends it
from his own account. Oregon Public Records Law: ORS 192.311 to 192.478. All 33 local health jurisdictions (36 counties) record their
licensing and inspections in one shared HealthSpace system that OHA's Food Safety Program runs, so one request to OHA could cover the
whole state. If OHA answers that the counties hold the records, the same text goes to the largest counties first (Multnomah,
Washington, Clackamas, Lane, Marion, Deschutes, Jackson).

Where: OHA's Public Records Request page, https://www.oregon.gov/oha/erd/pages/records.aspx (an online form; the form's entries
become a public record and may be listed online). By email: oha.publicrecords@odhsoha.oregon.gov (OHA's public records contact per that
page, as found 2026-10-24; check the page before sending). OHA says many requests finish in 14 days and most in 30.

> Under the Oregon Public Records Law (ORS 192.311 et seq.), I request an electronic export (CSV or Excel) from the statewide
> environmental health data system (HealthSpace) of food service inspections in all Oregon counties from January 1, 2024 to the
> present, with these fields where they exist:
> - facility (license) ID, facility name, facility type (restaurant, mobile unit, commissary, bed and breakfast, and so on),
>   street address, city, zip and county or local health jurisdiction, and license status;
> - for each inspection: date, inspection type (for example semi-annual, reinspection, complaint), the sanitation score, the result or
>   notice posted ("Complied" or "Failed to Comply", or a closure), and the number of Priority, Priority Foundation and Core violations.
>
> I don't need owner, operator or inspector names, or any personal information. The records will be used in a free, non-commercial
> consumer app and website (no advertising, no purchases, no resale) that shows each restaurant's official result as published,
> labeled with the county and date. Because the purpose is public information about public health, I ask that fees be waived or
> reduced under ORS 192.324(5); if there is a fee, please send an estimate before starting. A standard export or an existing report
> is fine. Please contact me at nick@eatsranked.com with any questions.

When the file arrives, save it in `data/raw/official/` and tell the or-eats session: `pipeline/official.py` gets a loader, and the app
shows each county's score and notice as official (never a grade of ours), with "records through" at least 14 days before the extract
(results post after 14 days). Mobile units (food carts) and commissaries are inspected but not scored, so carts get no score.
