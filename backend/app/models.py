from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

Status = Literal['maison', 'travail', 'exterieur', 'a_decider']
Unit = Literal['g', 'kg', 'ml', 'l', 'piece']
Amount = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=3)]
Nonnegative = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=3)]
Name = Annotated[str, Field(min_length=1, max_length=120)]


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Credentials(Input):
    name: Name
    password: Annotated[str, StringConstraints(strip_whitespace=False, min_length=12, max_length=128)]


class Ingredient(Input):
    name: Name
    dimension: Literal['masse', 'volume', 'piece']


class IngredientCreate(Ingredient):
    reuse_id: int | None = Field(default=None, gt=0)
    allow_distinct: bool = False


class IngredientMerge(Input):
    operation_id: UUID
    target_id: int = Field(gt=0)
    preview_token: str = Field(pattern=r'^[0-9a-f]{64}$')


class Line(Input):
    ingredient_id: int = Field(gt=0)
    quantity: Amount
    unit: Unit


class Recipe(Input):
    name: Name
    kind: Literal['simple', 'improvise', 'recette'] = 'recette'
    portions: int = Field(default=4, ge=1, le=30)
    steps: str = Field(default='', max_length=20000)
    minutes: int = Field(default=0, ge=0, le=1440)
    source_url: str = Field(default='', max_length=2000)
    source_author: str = Field(default='', max_length=300)
    ingredient_notes: str = Field(default='', max_length=12000)
    ingredients: list[Line] = Field(default_factory=list, max_length=100)

    @field_validator('source_url')
    @classmethod
    def source_is_http(cls, value):
        from urllib.parse import urlsplit
        if value and (urlsplit(value).scheme not in ('http', 'https') or not urlsplit(value).netloc):
            raise ValueError('La source doit être une URL HTTP ou HTTPS.')
        return value

    @model_validator(mode='after')
    def distinct_ingredients(self):
        if self.kind == 'simple' and self.ingredients:
            raise ValueError('Un intitulé simple ne contient pas de quantités.')
        if len({line.ingredient_id for line in self.ingredients}) != len(self.ingredients):
            raise ValueError('Regrouper les quantités d’un même ingrédient.')
        return self


class Presence(Input):
    day: int = Field(ge=0, le=6)
    slot: Literal['midi', 'soir']
    status: Status


class Settings(Input):
    portions: int = Field(ge=1, le=30)
    presence: list[Presence] = Field(min_length=14, max_length=14)

    @model_validator(mode='after')
    def complete(self):
        if len({(p.day, p.slot) for p in self.presence}) != 14:
            raise ValueError('Le modèle doit contenir les 14 créneaux distincts.')
        return self


class Week(Input):
    start: date


class Meal(Input):
    status: Status
    title: str = Field(default='', max_length=120)
    recipe_id: int | None = Field(default=None, gt=0)
    side_id: int | None = Field(default=None, gt=0)
    portions: int = Field(ge=1, le=30)


class Stock(Line):
    location: Name = 'Placard'
    expires: date | None = None


class Correction(Input):
    quantity: Nonnegative
    unit: Unit
    reason: str = Field(min_length=1, max_length=250)


class Preparation(Input):
    operation_id: UUID
    quantities: list[Line] | None = Field(default=None, max_length=200)

    @model_validator(mode='after')
    def distinct(self):
        if self.quantities is not None and len({x.ingredient_id for x in self.quantities}) != len(self.quantities):
            raise ValueError('Un ingrédient ne peut être confirmé qu’une fois.')
        return self


class Unpreparation(Input):
    operation_id: UUID
    preparation_id: UUID | None = None


class Manual(Line):
    pass


class Check(Input):
    checked: bool
    manual_id: int | None = Field(default=None, gt=0)
    ingredient_id: int | None = Field(default=None, gt=0)

    @model_validator(mode='after')
    def one_target(self):
        if (self.manual_id is None) == (self.ingredient_id is None):
            raise ValueError('Choisir exactement un article.')
        return self


class PurchaseLine(Line):
    manual_id: int | None = Field(default=None, gt=0)
    requested_ingredient_id: int | None = Field(default=None, gt=0)
    location: Name = 'Placard'
    expires: date | None = None


class Purchase(Input):
    operation_id: UUID
    items: list[PurchaseLine] = Field(min_length=1, max_length=200)


class ImportPreview(Input):
    mode: Literal['url', 'text'] = 'url'
    url: str = Field(default='', max_length=2000)
    text: str = Field(default='', max_length=60000)

    @model_validator(mode='after')
    def source_present(self):
        if self.mode == 'url' and not self.url:
            raise ValueError('Coller une URL publique.')
        if self.mode == 'text' and not self.text:
            raise ValueError('Coller le texte de la recette.')
        if self.url:
            Recipe(name='Source', source_url=self.url)
        return self


class ImportIngredient(Input):
    allow_distinct: bool = False
    ingredient_id: int | None = Field(default=None, gt=0)
    name: str = Field(default='', max_length=120)
    quantity: Amount
    unit: Unit

    @model_validator(mode='after')
    def name_or_reference(self):
        if self.ingredient_id is None and not self.name:
            raise ValueError('Choisir un ingrédient ou lui donner un nom.')
        return self


class PhotoDraft(Input):
    data_base64: str = Field(min_length=1, max_length=699052)
    source_url: str = Field(default='', max_length=2000)
    attribution: str = Field(default='', max_length=300)

    @field_validator('source_url')
    @classmethod
    def valid_source(cls, value):
        from .safe_fetch import validate_url
        return validate_url(value).url if value else ''


class PhotoSource(Input):
    url: str = Field(min_length=1, max_length=2000)
    attribution: str = Field(default='', max_length=300)

    @field_validator('url')
    @classmethod
    def public_url(cls, value):
        from .safe_fetch import validate_url
        return validate_url(value).url


class ImportConfirmation(Input):
    operation_id: UUID
    recipe: Recipe
    items: list[ImportIngredient] = Field(default_factory=list, max_length=100)
    photo: PhotoDraft | None = None

    @model_validator(mode='after')
    def one_list(self):
        if self.recipe.ingredients or self.recipe.kind != 'recette':
            raise ValueError('Utiliser les lignes de confirmation pour la recette importée.')
        return self


class RecipePreferences(Input):
    favorite: bool | None = None
    to_try: bool | None = None
    rating: Literal['', 'a_refaire', 'pas_mal', 'a_ameliorer', 'ne_plus_proposer'] | None = None
    category: Literal['autre', 'viande', 'poisson', 'legumes', 'vegetarien', 'feculents', 'dessert'] | None = None
    comment: str | None = Field(default=None, max_length=4000)
    variant: str | None = Field(default=None, max_length=12000)

    @model_validator(mode='after')
    def provided(self):
        if not self.model_fields_set or any(getattr(self, name) is None for name in self.model_fields_set):
            raise ValueError('Fournir au moins une préférence, sans valeur nulle.')
        return self


class CopyWeek(Input):
    operation_id: UUID
    source_start: date
    preview_token: str = Field(pattern=r'^[0-9a-f]{64}$')


class ReuseMeal(Input):
    operation_id: UUID
    source_meal_id: int = Field(gt=0)


class PlanSuggestion(Input):
    operation_id: UUID
    recipe_id: int = Field(gt=0)


class OfflineBase(Input):
    operation_id: UUID
    week_start: date


class OfflineCheck(OfflineBase):
    action: Literal['check']
    item_key: str = Field(pattern=r'^(auto|manual)-[1-9][0-9]{0,12}$')
    expected_version: str = Field(pattern=r'^[0-9a-f]{64}$')
    checked: bool


class OfflineAdd(OfflineBase):
    action: Literal['add']
    ingredient_id: int = Field(gt=0)
    quantity: Amount
    unit: Unit
    checked: bool = False


class OfflineEdit(OfflineBase):
    action: Literal['edit']
    item_key: str = Field(pattern=r'^manual-[1-9][0-9]{0,12}$')
    expected_version: str = Field(pattern=r'^[0-9a-f]{64}$')
    quantity: Amount
    unit: Unit
    checked: bool


class OfflineRemove(OfflineBase):
    action: Literal['remove']
    item_key: str = Field(pattern=r'^manual-[1-9][0-9]{0,12}$')
    expected_version: str = Field(pattern=r'^[0-9a-f]{64}$')


class OfflineSync(Input):
    household_id: UUID
    operations: list[Annotated[OfflineCheck | OfflineAdd | OfflineEdit | OfflineRemove, Field(discriminator='action')]] = Field(min_length=1, max_length=50)


class WebDiscovery(Input):
    source_id: int = Field(default=0, ge=0)
    exclude: list[Annotated[str, Field(max_length=2000)]] = Field(default_factory=list, max_length=100)


class WebSource(Input):
    url: str = Field(min_length=1, max_length=2000)
