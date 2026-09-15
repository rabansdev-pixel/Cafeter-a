from marshmallow import Schema, fields


class OriginSchema(Schema):
    id = fields.Int()
    country = fields.Str()
    region = fields.Str()
    farm = fields.Str()
    altitude_meters = fields.Int()
    process = fields.Str()
    variety = fields.Str()


class TastingProfileSchema(Schema):
    id = fields.Int()
    roast_level = fields.Str()
    acidity = fields.Int()
    body = fields.Int()
    sweetness = fields.Int()
    aroma = fields.Int()
    flavor_notes = fields.Str()
    notes = fields.Method("get_notes_list")

    def get_notes_list(self, obj):
        return obj.notes_list() if hasattr(obj, "notes_list") else []


class ProductSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    slug = fields.Str()
    tagline = fields.Str()
    description = fields.Str()
    price = fields.Float()
    formatted_price = fields.Method("get_formatted_price")
    stock = fields.Int()
    weight_grams = fields.Int()
    image_url = fields.Str(attribute="display_image_url")
    is_featured = fields.Bool()
    origin = fields.Nested(OriginSchema)
    tasting_profile = fields.Nested(TastingProfileSchema)

    def get_formatted_price(self, obj):
        price = getattr(obj, "price", 0.0)
        return f"${price:,.0f}".replace(",", ".")


product_schema = ProductSchema()
products_schema = ProductSchema(many=True)
