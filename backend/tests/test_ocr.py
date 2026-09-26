from app.services.ocr import _extract_fields

def test_extracts_barcode_and_fssai_separately():
    text = "ABC Crackers\nFSSAI Lic No 10012345000123\nSodium 890 mg\nSugar 3.1 g\nIngredients: wheat flour, salt"
    fields = _extract_fields(text, [{"type": "EAN_13", "value": "8901234567890"}])
    assert fields["barcodes"] == ["8901234567890"]
    assert fields["fssai_license"] == "10012345000123"
    assert fields["nutrition"]["sodium"] == 890
    assert fields["nutrition"]["sugar"] == 3.1
    assert fields["ingredients"] == ["wheat flour", "salt"]

def test_missing_evidence_stays_missing():
    fields = _extract_fields("ABC food label", [])
    assert fields["barcodes"] == []
    assert fields["nutrition"]["sodium"] is None
    assert fields["nutrition"]["sugar"] is None

def test_barcode_is_not_guessed_from_ocr_text():
    fields = _extract_fields("Printed digits 8901234567890", [])
    assert fields["barcodes"] == []
