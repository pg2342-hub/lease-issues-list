"""Write the constructed test leases and their answer key.

Each lease is assembled from clauses written for this repo. For every playbook position a lease
gets either a clause that matches the landlord's standard position, a clause that departs from
it, or nothing at all. The answer key is therefore known exactly, which the real filed leases
cannot give. Everything here is invented: parties, addresses, numbers.

    python scripts/make_constructed.py
"""

from __future__ import annotations

import random
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "leases" / "constructed"

STANDARD = {
    "assignment": (
        "Tenant shall not assign this Lease or sublet all or any part of the Premises without the prior written consent of "
        "Landlord in each instance. Before granting consent, Landlord may elect, by notice to Tenant within thirty (30) days "
        "after Tenant's request, to recapture the space proposed to be assigned or sublet. If Tenant receives rent or other "
        "consideration in excess of the Rent payable hereunder, Tenant shall pay Landlord fifty percent (50%) of such excess."
    ),
    "use": (
        "Tenant shall use the Premises solely for general, executive and administrative offices and for no other purpose. "
        "Tenant shall not change the use of the Premises without Landlord's prior written consent."
    ),
    "alterations": (
        "Tenant shall make no alterations, additions or improvements to the Premises without Landlord's prior written consent, "
        "except decorative work such as painting and carpeting. All work shall be performed by contractors approved by Landlord, "
        "and Tenant shall reimburse Landlord for its reasonable out-of-pocket costs of reviewing Tenant's plans."
    ),
    "restoration": (
        "On the expiration or earlier termination of the Term, Tenant shall, at its expense, remove all Specialty Alterations "
        "(including vaults, raised floors, internal staircases and supplemental air conditioning units) and repair any damage "
        "caused by their removal, whether or not Landlord designated them for removal when it consented to them."
    ),
    "operating_expenses": (
        "Tenant shall pay, as Additional Rent, Tenant's Proportionate Share of the amount by which Operating Expenses for each "
        "Operating Year exceed Operating Expenses for the Base Operating Year. There shall be no limit on the annual increase "
        "in Operating Expenses, whether controllable or not."
    ),
    "taxes": (
        "Tenant shall pay, as Additional Rent, Tenant's Proportionate Share of the amount by which Real Estate Taxes for each "
        "Tax Year exceed Real Estate Taxes for the Base Tax Year."
    ),
    "security_deposit": (
        "On signing this Lease, Tenant shall deliver to Landlord an unconditional, irrevocable letter of credit in the amount "
        "of the Security Amount. Landlord may draw on the letter of credit after any Event of Default. The Security Amount "
        "shall be reduced on the third anniversary of the Commencement Date, provided that no Event of Default has ever "
        "occurred under this Lease."
    ),
    "insurance": (
        "Tenant shall maintain commercial general liability insurance with limits of not less than Five Million Dollars "
        "($5,000,000) per occurrence, which may be met with primary and umbrella policies, naming Landlord and Landlord's "
        "managing agent as additional insureds. Landlord and Tenant each waive all rights of recovery against the other to "
        "the extent of insurance proceeds received, and each shall obtain a waiver of subrogation from its insurers."
    ),
    "indemnity": (
        "Tenant shall indemnify and hold Landlord harmless from all claims arising from the use or occupancy of the Premises "
        "or from any act or omission of Tenant or its employees, agents, contractors or invitees. Landlord shall indemnify "
        "Tenant only for claims arising from Landlord's negligence or willful misconduct."
    ),
    "landlord_liability": (
        "Tenant shall look solely to Landlord's interest in the Building for the recovery of any judgment against Landlord, "
        "and no other property or assets of Landlord or its principals shall be subject to levy. In no event shall Landlord "
        "be liable for consequential, indirect or special damages."
    ),
    "default": (
        "Each of the following is an Event of Default: (a) Tenant fails to pay any Rent within five (5) days after notice "
        "from Landlord; or (b) Tenant fails to perform any other obligation within thirty (30) days after notice from "
        "Landlord, provided that if the failure cannot reasonably be cured within thirty (30) days, the period shall be "
        "extended for so long as Tenant diligently pursues the cure."
    ),
    "casualty": (
        "If the Premises are damaged by fire or other casualty, Landlord shall restore the Building and the Premises. Rent "
        "shall abate in proportion to the part of the Premises rendered unusable. If Landlord has not substantially completed "
        "the restoration within fifteen (15) months after the casualty, Tenant may terminate this Lease by notice to Landlord."
    ),
    "holdover": (
        "If Tenant remains in possession after the end of the Term, Tenant shall pay for each month of holdover one hundred "
        "fifty percent (150%) of the Rent for the last month of the Term for the first sixty (60) days, and two hundred "
        "percent (200%) thereafter. If Tenant remains in possession more than thirty (30) days after notice from Landlord, "
        "Tenant shall also be liable for all damages Landlord suffers, including consequential damages."
    ),
    "options": (
        "Tenant shall have no option to renew or extend the Term, no right to lease additional space in the Building and no "
        "right to terminate this Lease before the Expiration Date."
    ),
    "law_and_jury": (
        "This Lease shall be governed by the laws of the State of New York. Landlord and Tenant each waive trial by jury in "
        "any action arising out of this Lease."
    ),
}

DEPARTS = {
    "assignment": (
        "Tenant may assign this Lease or sublet all or any part of the Premises with the consent of Landlord, which consent "
        "shall not be unreasonably withheld, conditioned or delayed. Landlord shall have no right to recapture the Premises, "
        "and Tenant shall be entitled to retain any rent or other consideration received from an assignee or subtenant."
    ),
    "use": "Tenant may use the Premises for any lawful purpose.",
    "alterations": (
        "Tenant may make non-structural alterations that do not affect the Building systems without Landlord's consent, "
        "provided that the cost of any single project does not exceed Two Hundred Fifty Thousand Dollars ($250,000). "
        "Landlord's consent to any other alteration shall not be unreasonably withheld."
    ),
    "restoration": (
        "Tenant shall have no obligation to remove any alterations or to restore the Premises at the end of the Term, other "
        "than items Landlord designated for removal in writing at the time it approved the plans for them."
    ),
    "operating_expenses": (
        "Tenant shall pay, as Additional Rent, Tenant's Proportionate Share of the amount by which Operating Expenses for each "
        "Operating Year exceed Operating Expenses for the Base Operating Year, provided that Controllable Operating Expenses "
        "included in that calculation shall not increase by more than three percent (3%) per year on a cumulative basis."
    ),
    "taxes": ("Tenant shall have no obligation to pay any share of Real Estate Taxes, which are included in the Fixed Rent."),
    "security_deposit": (
        "On signing this Lease, Tenant shall deliver to Landlord an unconditional, irrevocable letter of credit in the amount "
        "of the Security Amount. The Security Amount shall be reduced by one-half on the second anniversary of the "
        "Commencement Date, whether or not any default has previously occurred."
    ),
    "insurance": (
        "Tenant shall maintain commercial general liability insurance with limits of not less than One Million Dollars "
        "($1,000,000) per occurrence. Landlord waives all rights of recovery against Tenant for any loss covered by "
        "Landlord's property insurance."
    ),
    "indemnity": (
        "Landlord shall indemnify and hold Tenant harmless from all claims arising from any occurrence in the Building or its "
        "common areas. Tenant shall indemnify Landlord only for claims arising from Tenant's gross negligence or willful "
        "misconduct."
    ),
    "landlord_liability": (
        "Landlord shall be liable to Tenant for all damages, including consequential damages and lost profits, arising from "
        "Landlord's breach of this Lease."
    ),
    "default": (
        "Each of the following is an Event of Default: (a) Tenant fails to pay any Rent within thirty (30) days after a "
        "second written notice from Landlord; or (b) Tenant fails to perform any other obligation within sixty (60) days "
        "after notice from Landlord."
    ),
    "casualty": (
        "If the Premises are damaged by fire or other casualty and Landlord's architect estimates that restoration will take "
        "more than one hundred twenty (120) days, Tenant may terminate this Lease by notice to Landlord. Rent shall abate in "
        "full until the restoration is complete."
    ),
    "holdover": (
        "If Tenant remains in possession after the end of the Term, Tenant shall pay for each month of holdover the Rent in "
        "effect for the last month of the Term, and Tenant shall not be liable for any other damages."
    ),
    "options": (
        "Tenant shall have one option to extend the Term for five (5) years at ninety percent (90%) of the Fixed Rent payable "
        "in the last year of the initial Term, and a right of first offer on any space that becomes available on the floor "
        "above the Premises."
    ),
    "law_and_jury": "This Lease shall be governed by the laws of the State of Delaware.",
}

FRAME = [
    (
        "PREMISES",
        'Landlord leases to Tenant, and Tenant hires from Landlord, the entire {floor} floor (the "Premises") of the building known as {address}, New York, New York (the "Building").',
    ),
    (
        "TERM",
        'The term of this Lease (the "Term") begins on the Commencement Date and ends on the last day of the month in which the tenth anniversary of the Commencement Date falls (the "Expiration Date").',
    ),
    (
        "FIXED RENT",
        "Tenant shall pay Fixed Rent at the annual rate set out in Schedule A, in equal monthly installments in advance on the first day of each month.",
    ),
    (
        "SERVICES",
        "Landlord shall provide passenger elevator service, heat and air conditioning during Business Hours, and cleaning of the Premises in accordance with Schedule B.",
    ),
]

ORDER = list(STANDARD)
TITLES = {
    "assignment": "ASSIGNMENT AND SUBLETTING",
    "use": "USE",
    "alterations": "ALTERATIONS",
    "restoration": "END OF TERM",
    "operating_expenses": "OPERATING EXPENSES",
    "taxes": "TAXES",
    "security_deposit": "SECURITY",
    "insurance": "INSURANCE",
    "indemnity": "INDEMNITY",
    "landlord_liability": "LANDLORD'S LIABILITY",
    "default": "DEFAULT",
    "casualty": "FIRE OR OTHER CASUALTY",
    "holdover": "HOLDING OVER",
    "options": "OPTIONS",
    "law_and_jury": "GOVERNING LAW; JURY WAIVER",
}


def build(seed: int) -> tuple[str, dict]:
    rng = random.Random(seed)
    tenant = [
        "Harbor Vale Analytics LLC",
        "Pemberton Fielding Inc.",
        "Coalport Media Group LLC",
        "Ashgrove Partners LP",
        "Kestrel Ridge Health Inc.",
        "Northline Software Corp.",
    ][seed % 6]
    address = [
        "412 Halden Street",
        "77 Corliss Avenue",
        "1150 Wexford Place",
        "23 Tamsin Lane",
        "600 Orrin Street",
        "88 Bellmore Plaza",
    ][seed % 6]
    floor = ["fourth", "ninth", "twelfth", "sixth", "fifteenth", "twentieth"][seed % 6]
    answers = {}
    clauses = []
    for pid in ORDER:
        roll = rng.random()
        if roll < 0.45:
            answers[pid] = "consistent"
            clauses.append((pid, STANDARD[pid]))
        elif roll < 0.85:
            answers[pid] = "departs"
            clauses.append((pid, DEPARTS[pid]))
        else:
            answers[pid] = "not_found"
    articles = [(t, b.format(floor=floor, address=address)) for t, b in FRAME]
    for pid, text in clauses:
        articles.append((TITLES[pid], text))
    lines = [
        "AGREEMENT OF LEASE",
        "",
        f'THIS AGREEMENT OF LEASE is made between Halden Owner LLC ("Landlord") and {tenant} ("Tenant").',
        "All names, addresses and figures in this lease are invented for testing.",
        "",
    ]
    for n, (title, body) in enumerate(articles, 1):
        lines += [f"ARTICLE {n}. {title}", "", f"{n}.1 {body}", ""]
    return "\n".join(lines), answers


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    key = {}
    for seed in range(6):
        text, answers = build(seed)
        lid = f"constructed-{seed + 1}"
        (OUT / f"{lid}.txt").write_text(text, encoding="utf-8")
        key[lid] = answers
    (OUT / "answers.yml").write_text(
        "# Expected status for every playbook position in each constructed lease.\n" + yaml.safe_dump(key, sort_keys=True),
        encoding="utf-8",
    )
    print(f"wrote {len(key)} constructed leases to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
