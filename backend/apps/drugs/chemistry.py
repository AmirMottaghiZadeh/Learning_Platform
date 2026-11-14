"""PubChem enrichment and local RDKit depictions. Never infer identity from a formula."""
import hashlib
import json
import re
import time
import threading
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.db import transaction
from django.utils import timezone

from .models import ChemistryReview, Ingredient, IngredientChemistry

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
_rate_lock = threading.Lock()
_last_request = 0.0


class ChemistryError(ValueError):
    pass


def _formula_signature(formula):
    """Compare atom counts and charge, allowing different element ordering."""
    charge = 0
    match = re.search(r"([+-])(\d*)$", formula)
    if match:
        charge = (1 if match[1] == "+" else -1) * int(match[2] or "1")
        formula = formula[:match.start()]
    if not re.fullmatch(r"(?:[A-Z][a-z]?\d*)+", formula):
        return None
    counts = {}
    for element, amount in re.findall(r"([A-Z][a-z]?)(\d*)", formula):
        counts[element] = counts.get(element, 0) + int(amount or "1")
    return counts, charge


def _get(path):
    global _last_request
    # Shared by importer workers: at most 4 requests/sec including retries.
    for attempt in range(3):
        with _rate_lock:
            time.sleep(max(0, 0.26 - (time.monotonic() - _last_request)))
            _last_request = time.monotonic()
        try:
            req = Request(BASE + path, headers={"User-Agent": "Pharmenta-Chemistry/1.0", "Accept": "application/json"})
            with urlopen(req, timeout=20) as response:
                return json.load(response)
        except HTTPError as exc:
            if exc.code == 404:
                return None
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise ChemistryError(f"PubChem HTTP {exc.code}") from exc
            time.sleep(2 ** attempt)
        except (URLError, TimeoutError, ValueError) as exc:
            if attempt == 2:
                raise ChemistryError("PubChem unavailable or invalid response") from exc
            time.sleep(2 ** attempt)


def depiction(smiles, expected_formula):
    from rdkit import Chem
    from rdkit.Chem import rdMolDescriptors
    from rdkit.Chem.Draw import rdMolDraw2D

    if len(smiles) > 20000:
        raise ChemistryError("Structure too large for a small-molecule depiction")
    mol = Chem.MolFromSmiles(smiles)
    if mol is None or not mol.GetNumAtoms() or mol.GetNumAtoms() > 500:
        raise ChemistryError("Invalid or oversized molecular structure")
    formula = rdMolDescriptors.CalcMolFormula(mol)
    actual, expected = _formula_signature(formula), _formula_signature(expected_formula)
    if formula != expected_formula and (actual is None or expected is None or actual != expected):
        raise ChemistryError(f"Formula mismatch: PubChem={expected_formula}, RDKit={formula}")
    drawer = rdMolDraw2D.MolDraw2DSVG(640, 360)
    drawer.drawOptions().clearBackground = True
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
    drawer.FinishDrawing()
    return drawer.GetDrawingText()


def fetch_candidate(name, cid=None):
    if cid is not None and (not isinstance(cid, int) or isinstance(cid, bool) or cid <= 0):
        raise ChemistryError("Invalid PubChem CID")
    properties = "MolecularFormula,SMILES,InChIKey,Title"
    if cid is None:
        props = _get(f"/compound/name/{quote(name, safe='')}/property/{properties}/JSON?name_type=complete")
        rows = (props or {}).get("PropertyTable", {}).get("Properties", [])
        if not rows:
            return {"status": "not_found", "candidates": []}
        if len(rows) != 1:
            return {"status": "ambiguous", "candidates": [r["CID"] for r in rows[:50]]}
        cid = rows[0]["CID"]
    else:
        props = _get(f"/compound/cid/{cid}/property/{properties}/JSON")
        rows = (props or {}).get("PropertyTable", {}).get("Properties", [])
    if not isinstance(cid, int) or cid <= 0:
        raise ChemistryError("Invalid PubChem CID")
    if len(rows) != 1 or rows[0].get("CID") != cid:
        raise ChemistryError("PubChem compound not found")
    row = rows[0]
    smiles, formula = row.get("SMILES", ""), row.get("MolecularFormula", "")
    if not smiles or not formula or len(formula) > 512:
        raise ChemistryError("Compound has no supported formula/structure")
    return {"status": "pending", "pubchem_cid": cid, "matched_name": row.get("Title", "")[:255],
            "molecular_formula": formula, "smiles": smiles, "inchikey": row.get("InChIKey", ""),
            "structure_svg": depiction(smiles, formula), "candidates": [cid]}


def version(chemistry):
    if chemistry is None:
        return "missing"
    data = {f: getattr(chemistry, f) for f in (
        "status", "pubchem_cid", "matched_name", "molecular_formula", "smiles", "inchikey", "structure_svg",
        "ingredient_name", "ingredient_rxcui",
    )}
    data["updated_at"] = chemistry.updated_at.isoformat()
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def _audit(ingredient, chemistry, actor, action):
    ChemistryReview.objects.create(ingredient=ingredient, actor=actor, action=action, snapshot={
        "status": chemistry.status, "cid": chemistry.pubchem_cid, "formula": chemistry.molecular_formula,
        "smiles": chemistry.smiles, "inchikey": chemistry.inchikey, "matched_name": chemistry.matched_name,
        "ingredient_name": chemistry.ingredient_name, "ingredient_rxcui": chemistry.ingredient_rxcui,
        "fetched_at": chemistry.fetched_at.isoformat() if chemistry.fetched_at else None,
    })


def enrich(ingredient, *, cid=None, actor="import_pubchem", expected=None):
    # Do network/CPU work before acquiring locks. Preserve an existing review if it changed meanwhile.
    before = IngredientChemistry.objects.filter(ingredient=ingredient).first()
    initial = version(before)
    if expected is not None and expected != initial:
        raise ChemistryError("اطلاعات تغییر کرده؛ صفحه را دوباره باز کنید.")
    values = fetch_candidate(ingredient.name, cid)
    with transaction.atomic():
        actual = Ingredient.objects.select_for_update().get(pk=ingredient.pk)
        if (actual.name, actual.rxcui) != (ingredient.name, ingredient.rxcui):
            raise ChemistryError("هویت دارو تغییر کرده؛ دوباره دریافت کنید.")
        current = IngredientChemistry.objects.filter(ingredient=ingredient).first()
        if version(current) != initial:
            raise ChemistryError("اطلاعات هم‌زمان تغییر کرده؛ دوباره تلاش کنید.")
        chemistry = current or IngredientChemistry(ingredient=ingredient)
        for field in ("pubchem_cid", "matched_name", "molecular_formula", "smiles", "inchikey", "structure_svg"):
            setattr(chemistry, field, None if field == "pubchem_cid" else "")
        for key, value in values.items():
            setattr(chemistry, key, value)
        chemistry.reviewed_at = None
        chemistry.reviewed_by = ""
        chemistry.fetched_at = timezone.now()
        chemistry.ingredient_name = ingredient.name
        chemistry.ingredient_rxcui = ingredient.rxcui
        chemistry.save()
        _audit(ingredient, chemistry, actor, "fetch")
        return chemistry


@transaction.atomic
def review(ingredient, actor, action, expected):
    actual = Ingredient.objects.select_for_update().get(pk=ingredient.pk)
    chemistry = IngredientChemistry.objects.filter(ingredient=ingredient).first()
    if not chemistry or version(chemistry) != expected:
        raise ChemistryError("اطلاعات تغییر کرده؛ صفحه را دوباره باز کنید.")
    if action not in ("approve", "reject"):
        raise ChemistryError("اقدام نامعتبر است.")
    if action == "approve":
        if (actual.name, actual.rxcui) != (chemistry.ingredient_name, chemistry.ingredient_rxcui):
            raise ChemistryError("هویت دارو تغییر کرده؛ دوباره دریافت کنید.")
        if chemistry.status != "pending" or not chemistry.pubchem_cid:
            raise ChemistryError("ابتدا ترکیب معتبر را دریافت کنید.")
        # Revalidate the source formula against the saved stereochemical structure.
        chemistry.structure_svg = depiction(chemistry.smiles, chemistry.molecular_formula)
    chemistry.status = "approved" if action == "approve" else "rejected"
    chemistry.reviewed_by = actor
    chemistry.reviewed_at = timezone.now()
    chemistry.save()
    _audit(ingredient, chemistry, actor, action)
    return chemistry
