from sonde.publication import image_detour


def test_categories_de_ce_matin():
    assert image_detour("Régulation") == "regulation"
    assert image_detour("Cinéma") == "pop-culture-cinema"
    assert image_detour("Musique") == "pop-culture-vinyle"
    assert image_detour("Logiciel") == "logiciel"
    assert image_detour("IA") == "logiciel"
    assert image_detour("Mathématiques") == "savoir"


def test_titre_en_secours_puis_defaut():
    assert image_detour("Autre", "DMA : la conformité de façade des géants") == "regulation"
    assert image_detour("Divers", "Un titre sans indice") == "innovation"
    assert image_detour(None, None) == "innovation"


def test_puces():
    assert image_detour("Matériel") == "puces"
    assert image_detour(None, "Nvidia livre ses GPU aux clouds européens") == "puces"
    assert image_detour("IA") == "logiciel"
