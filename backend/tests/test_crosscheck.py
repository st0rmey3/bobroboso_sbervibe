from app.crosscheck import cross_checks, same_person


def slot(label, **fields):
    return {"label": label, "fields": {k: {"value": v} for k, v in fields.items()}}


def test_cyrillic_and_latin_spellings_of_one_person():
    assert same_person("ХАКИМОВ ТИМУР КАМОЛИДДИН УГЛИ", "HAKIMOV TIMUR")
    assert same_person("Сидоренко Андрей", "SIDARENKA ANDREI")
    assert same_person("Киселёв Максим", "КИСЕЛЕВ МАКСИМ ВАСИЛЬЕВИЧ")  # ё, case, missing patronymic


def test_different_people():
    assert not same_person("НеМаксим Чернецов", "КИСЕЛЕВ МАКСИМ ВАСИЛЬЕВИЧ")
    assert not same_person("Иванов Иван", "Петров Иван")


def test_typed_name_mismatch_is_reported():
    out = cross_checks("НеМаксим Чернецов", [slot("Паспорт РФ", full_name="КИСЕЛЕВ МАКСИМ ВАСИЛЬЕВИЧ")])
    assert out and "НеМаксим Чернецов" in out[0] and "Паспорт РФ" in out[0]


def test_documents_disagree_on_name_and_birth_date():
    out = cross_checks(
        "Хакимов Тимур",
        [
            slot("Паспорт", full_name="HAKIMOV TIMUR", birth_date="1984-08-19"),
            slot("Патент", full_name="ТОШПУЛАТОВ ДИЛШОД", birth_date="1989-03-12"),
        ],
    )
    assert any("ФИО различается" in w for w in out)
    assert any("Дата рождения различается" in w for w in out)


def test_consistent_application_has_no_warnings():
    out = cross_checks(
        "Киселев Максим Васильевич",
        [
            slot("Паспорт РФ", full_name="КИСЕЛЕВ МАКСИМ ВАСИЛЬЕВИЧ", birth_date="1980-07-19"),
            slot("СНИЛС", full_name="КИСЕЛЕВ МАКСИМ ВАСИЛЬЕВИЧ"),
        ],
    )
    assert out == []
