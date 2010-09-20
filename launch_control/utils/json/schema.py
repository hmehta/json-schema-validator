#!/usr/bin/python
"""
JSON schema validator for python
Note: only a subset of schema features are currently supported.

See: json-schema.org for details
"""
import decimal
import itertools
import re
import types

# Global configuration,
# List of types recognized as numeric
NUMERIC_TYPES = (int, float, decimal.Decimal)


class SchemaError(ValueError):
    """
    A bug in the schema prevents the program from working
    """


class ValidationError(ValueError):
    """
    A bug in the validated object prevents the program from working
    """


class Schema(object):
    """
    JSON schema object
    """

    def __init__(self, json_obj):
        """
        Initialize schema with JSON object

        Note: JSON objects are just plain python dictionaries
        """
        if not isinstance(json_obj, dict):
            raise SchemaError("Schema definition must be a JSON object")
        self._schema = json_obj

    def __repr__(self):
        return "Schema({0!r})".format(self._schema)

    @property
    def type(self):
        """
        Return the 'type' property of this schema.

        The return value is always a list of correct JSON types.
        Correct JSON types are one of the pre-defined simple types or
        another schema object. 

        List of built-in simple types:
            * 'string'
            * 'number'
            * 'integer'
            * 'boolean'
            * 'object'
            * 'array'
            * 'any' (default)
        """
        value = self._schema.get("type", "any")
        if not isinstance(value, (basestring, dict, list)):
            raise SchemaError(
                "type value {0!r} is not a simple type name, nested "
                "schema nor a list of those".format( value))
        if isinstance(value, list):
            type_list = value
        else:
            type_list = [value]
        seen = set()
        for js_type in type_list:
            if isinstance(js_type, dict):
                # no nested validation here
                pass
            else:
                if js_type in seen:
                    raise SchemaError(
                        "type value {0!r} contains duplicate element"
                        " {1!r}".format( value, js_type))
                else:
                    seen.add(js_type)
                if js_type not in (
                    "string", "number", "integer", "boolean", "object",
                    "array", "null", "any"):
                    raise SchemaError(
                        "type value {0!r} is not a simple type "
                        "name".format(js_type))
        return type_list

    @property
    def properties(self):
        value = self._schema.get("properties", {})
        if not isinstance(value, dict):
            raise SchemaError(
                "properties value {0!r} is not an object".format(value))
        return value

    @property
    def items(self):
        value = self._schema.get("items", {})
        if not isinstance(value, (list, dict)):
            raise SchemaError(
                "items value {0!r} is neither a list nor an object".
                format(value))
        return value

    @property
    def optional(self):
        value = self._schema.get("optional", False)
        if value is not False and value is not True:
            raise SchemaError(
                "optional value {0!r} is not a boolean".format(value))
        return value

    @property
    def additionalProperties(self):
        value = self._schema.get("additionalProperties", {})
        if not isinstance(value, dict) and value is not False:
            raise SchemaError(
                "additionalProperties value {0!r} is neither false nor"
                " an object".format(value))
        return value

    @property
    def requires(self): 
        value = self._schema.get("requires", {})
        if not isinstance(value, (basestring, dict)):
            raise SchemaError(
                "requires value {0!r} is neither a string nor an"
                " object".format(value))
        return value

    @property
    def minimum(self):
        value = self._schema.get("minimum", None)
        if value is None:
            return
        if not isinstance(value, NUMERIC_TYPES):
            raise SchemaError(
                "minimum value {0!r} is not a numeric type".format(
                    value))
        return value

    @property
    def maximum(self):
        value = self._schema.get("maximum", None)
        if value is None:
            return
        if not isinstance(value, NUMERIC_TYPES):
            raise SchemaError(
                "maximum value {0!r} is not a numeric type".format(
                    value))
        return value

    @property
    def minimumCanEqual(self):
        if self.minimum is None:
            raise SchemaError("minimumCanEqual requires presence of minimum")
        value = self._schema.get("minimumCanEqual", True)
        if value is not True and value is not False:
            raise SchemaError(
                "minimumCanEqual value {0!r} is not a boolean".format(
                    value))
        return value

    @property
    def maximumCanEqual(self):
        if self.maximum is None:
            raise SchemaError("maximumCanEqual requires presence of maximum")
        value = self._schema.get("maximumCanEqual", True)
        if value is not True and value is not False:
            raise SchemaError(
                "maximumCanEqual value {0!r} is not a boolean".format(
                    value))
        return value

    @property
    def minItems(self):
        value = self._schema.get("minItems", 0)
        if not isinstance(value, int):
            raise SchemaError(
                "minItems value {0!r} is not an integer".format(value))
        if value < 0:
            raise SchemaError(
                "minItems value {0!r} cannot be negative".format(value))
        return value

    @property
    def maxItems(self):
        value = self._schema.get("maxItems", None)
        if value is None:
            return
        if not isinstance(value, int):
            raise SchemaError(
                "maxItems value {0!r} is not an integer".format(value))
        return value

    @property
    def uniqueItems(self):
        value = self._schema.get("uniqueItems", False)
        if value is not True and value is not False:
            raise SchemaError(
                "uniqueItems value {0!r} is not a boolean".format(value))
        return value

    @property
    def pattern(self):
        """
        Note: JSON schema specifications says that this value SHOULD
        follow the EMCA 262/Perl 5 format. We cannot support this so we
        support python regular expressions instead. This is still valid
        but should be noted for clarity.

        The return value is either None or a compiled regular expression
        object
        """
        value = self._schema.get("pattern", None)
        if value is None:
            return
        try:
            return re.compile(value)
        except re.error as ex:
            raise SchemaError(
                "pattern value {0!r} is not a valid regular expression:"
                " {1}".format(value, str(ex)))

    @property
    def minLength(self):
        value = self._schema.get("minLength", 0)
        if not isinstance(value, int):
            raise SchemaError(
                "minLength value {0!r} is not an integer".format(value))
        if value < 0:
            raise SchemaError(
                "minLength value {0!r} cannot be negative".format(value))
        return value

    @property
    def maxLength(self):
        value = self._schema.get("maxLength", None)
        if value is None:
            return
        if not isinstance(value, int):
            raise SchemaError(
                "maxLength value {0!r} is not an integer".format(value))
        return value

    @property
    def enum(self):
        value = self._schema.get("enum", None)
        if value is None:
            return
        if not isinstance(value, list):
            raise SchemaError(
                "enum value {0!r} is not a list".format(value))
        if len(value) == 0:
            raise SchemaError(
                "enum value {0!r} does not contain any"
                " elements".format(value))
        seen = set()
        for item in value:
            if item in seen:
                raise SchemaError(
                    "enum value {0!r} contains duplicate element"
                    " {1!r}".format(value, item))
            else:
                seen.add(item)
        return value
    
    @property
    def title(self):
        value = self._schema.get("title", None)
        if value is None:
            return
        if not isinstance(value, basestring):
            raise SchemaError(
                "title value {0!r} is not a string".format(value))
        return value

    @property
    def description(self):
        value = self._schema.get("description", None)
        if value is None:
            return
        if not isinstance(value, basestring):
            raise SchemaError(
                "description value {0!r} is not a string".format(value))
        return value

    @property
    def format(self):
        value = self._schema.get("format", None)
        if value is None:
            return
        if not isinstance(value, basestring):
            raise SchemaError(
                "format value {0!r} is not a string".format(value))
        if value in [
            'date-time',
        ]:
            return value
        raise NotImplementedError(
            "format value {0!r} is not supported".format(value))

    @property
    def contentEncoding(self):
        value = self._schema.get("contentEncoding", None)
        if value is None:
            return
        if value.lower() not in [
            "7bit", "8bit", "binary", "quoted-printable", "base64",
            "ietf-token", "x-token"]:
            raise SchemaError(
                "contentEncoding value {0!r} is not"
                " valid".format(value))
        if value.lower() != "base64":
            raise NotImplementedError(
                "contentEncoding value {0!r} is not supported".format(
                    value))
        return value

    @property
    def divisibleBy(self):
        value = self._schema.get("divisibleBy", 1)
        if value is None:
            return
        if not isinstance(value, NUMERIC_TYPES):
            raise SchemaError(
                "divisibleBy value {0!r} is not a numeric type".
                format(value))
        if value < 0:
            raise SchemaError(
                "divisibleBy value {0!r} cannot be"
                " negative".format(value))
        return value
    
    @property
    def disallow(self):
        value = self._schema.get("disallow", None)
        if value is None:
            return
        if not isinstance(value, (basestring, dict, list)):
            raise SchemaError(
                "disallow value {0!r} is not a simple type name, nested "
                "schema nor a list of those".format( value))
        if isinstance(value, list):
            disallow_list = value
        else:
            disallow_list = [value]
        seen = set()
        for js_disallow in disallow_list:
            if isinstance(js_disallow, dict):
                # no nested validation here
                pass
            else:
                if js_disallow in seen:
                    raise SchemaError(
                        "disallow value {0!r} contains duplicate element"
                        " {1!r}".format(value, js_disallow))
                else:
                    seen.add(js_disallow)
                if js_disallow not in (
                    "string", "number", "integer", "boolean", "object",
                    "array", "null", "any"):
                    raise SchemaError(
                        "disallow value {0!r} is not a simple type"
                        " name".format(js_disallow))
        return disallow_list

    @property
    def extends(self):
        raise NotImplementedError("extends property is not supported")


class Validator(object):
    """
    JSON Schema validator.
    """
    JSON_TYPE_MAP = {
        "string": basestring,
        "number": NUMERIC_TYPES,
        "integer": int,
        "object": dict,
        "array": list,
        "null": types.NoneType,
    }

    def __init__(self):
        self._obj_stack = []

    @classmethod
    def validate(cls, schema, obj):
        """
        Validate specified JSON object obj with specified Schema
        instance schema.

        Returns True on success.
        Raises ValidationError if the object does not match schema.
        Raises SchemaError if the schema itself is wrong.
        """
        if not isinstance(schema, Schema):
            raise ValueError(
                "schema value {0!r} is not a Schema"
                " object".format(schema))
        cls()._validate_no_push(schema, obj)
        return True

    def _validate(self, schema, obj):
        self._obj_stack.append(obj)
        try:
            self._validate_no_push(schema, obj)
        finally:
            self._obj_stack.pop()

    def _validate_no_push(self, schema, obj):
        self._validate_type(schema, obj)
        self._validate_requires(schema, obj)
        if isinstance(obj, dict):
            self._obj_stack.append(obj)
            self._validate_properties(schema, obj)
            self._validate_additional_properties(schema, obj)
            self._obj_stack.pop()
        elif isinstance(obj, list):
            self._obj_stack.append(obj)
            self._validate_items(schema, obj)
            self._obj_stack.pop()
        else:
            self._validate_enum(schema, obj)
        self._report_unsupported(schema)

    def _report_unsupported(self, schema):
        if schema.minimum is not None:
            raise NotImplementedError("minimum is not supported")
        if schema.maximum is not None:
            raise NotImplementedError("maximum is not supported")
        if schema.minItems != 0:
            raise NotImplementedError("minItems is not supported")
        if schema.maxItems is not None:
            raise NotImplementedError("maxItems is not supported")
        if schema.uniqueItems != False:
            raise NotImplementedError("uniqueItems is not supported")
        if schema.pattern is not None:
            raise NotImplementedError("pattern is not supported")
        if schema.minLength != 0:
            raise NotImplementedError("minLength is not supported")
        if schema.maxLength is not None:
            raise NotImplementedError("maxLength is not supported")
        if schema.format is not None:
            raise NotImplementedError("format is not supported")
        if schema.contentEncoding is not None:
            raise NotImplementedError("contentEncoding is not supported")
        if schema.divisibleBy != 1:
            raise NotImplementedError("divisibleBy is not supported")
        if schema.disallow is not None:
            raise NotImplementedError("disallow is not supported")

    def _validate_type(self, schema, obj):
        for json_type in schema.type:
            if json_type == "any":
                return
            if json_type == "boolean":
                # Bool is special cased because in python there is no
                # way to test for isinstance(something, bool) that would
                # not catch isinstance(1, bool) :/
                if obj is not True and obj is not False:
                    raise ValidationError(
                        "{obj!r} does not match type {type!r}".format(
                            obj=obj, type=json_type))
                break
            elif isinstance(json_type, dict):
                # Nested type check. This is pretty odd case. Here we
                # don't change our object stack (it's the same object).
                self._validate_no_push(Schema(json_type), obj)
                break
            else:
                # Simple type check
                if isinstance(obj, self.JSON_TYPE_MAP[json_type]):
                    # First one that matches, wins
                    break
        else:
            raise ValidationError(
                "{obj!r} does not match type {type!r}".format(
                    obj=obj, type=json_type))

    def _validate_properties(self, schema, obj):
        assert isinstance(obj, dict)
        for prop, prop_schema_data in schema.properties.iteritems():
            prop_schema = Schema(prop_schema_data)
            if prop in obj:
                self._validate(prop_schema, obj[prop])
            else:
                if not prop_schema.optional:
                    raise ValidationError(
                        "{obj!r} does not have property"
                        " {prop!r}".format( obj=obj, prop=prop))

    def _validate_additional_properties(self, schema, obj):
        assert isinstance(obj, dict)
        if schema.additionalProperties is False:
            # Additional properties are disallowed
            # Report exception for each unknown property
            for prop in obj.iterkeys():
                if prop not in schema.properties:
                    raise ValidationError(
                        "{obj!r} has unknown property {prop!r} and"
                        " additionalProperties is false".format(
                            obj=obj, prop=prop))
        else:
            additional_schema = Schema(schema.additionalProperties)
            # Check each property against this object
            for prop_value in obj.itervalues(): 
                self._validate(additional_schema, prop_value)

    def _validate_enum(self, schema, obj):
        if schema.enum is not None:
            for allowed_value in schema.enum:
                if obj == allowed_value:
                    break
            else:
                raise ValidationError(
                    "{obj!r} does not match any value in enumeration"
                    " {enum!r}".format(obj=obj, enum=schema.enum))

    def _validate_items(self,  schema, obj):
        assert isinstance(obj, list)
        items_schema_json = schema.items
        if items_schema_json == {}:
            # default value, don't do anything
            return
        if isinstance(items_schema_json, dict):
            items_schema = Schema(items_schema_json)
            for item in obj:
                self._validate(items_schema, item)
        elif isinstance(items_schema_json, list):
            if len(obj) < len(items_schema_json):
                # If our array is shorter than the schema then
                # validation fails. Longer arrays are okay (during this
                # step) as they are validated based on
                # additionalProperties schema
                raise ValidationError(
                    "{obj!r} is shorter than array schema {schema!r}".
                    format(obj=obj, schema=items_schema_json))
            if len(obj) != len(items_schema_json) and schema.additionalProperties is False:
                # If our array is not exactly the same size as the
                # schema and additional properties are disallowed then
                # validation fails
                raise ValidationError(
                    "{obj!r} is not of the same length as array schema"
                    " {schema!r} and additionalProperties is"
                    " false".format(obj=obj, schema=items_schema_json))
            # Validate each array element using schema for the
            # corresponding array index, fill missing values (since
            # there may be more items in our array than in the schema)
            # with additionalProperties which by now is not False
            for item, item_schema_json in itertools.izip_longest(
                obj, items_schema_json, fillvalue=schema.additionalProperties):
                item_schema = Schema(item_schema_json)
                self._validate(item_schema, item)

    def _validate_requires(self, schema, obj):
        requires_json = schema.requires
        if requires_json == {}:
            # default value, don't do anything
            return
        # Find our enclosing object in the object stack
        if len(self._obj_stack) < 2:
            raise ValidationError(
                "{obj!r} requires that enclosing object matches"
                " schema {schema!r} but there is no enclosing"
                " object".format(obj=obj, schema=requires_json))
        # Note: Parent object can be None, (e.g. a null property)
        parent_obj = self._obj_stack[-2]
        if isinstance(requires_json, basestring):
            # This is a simple property test
            if (not isinstance(parent_obj, dict) 
                or requires_json not in parent_obj):
                raise ValidationError(
                    "{obj!r} requires presence of property {requires!r}"
                    " in the same object".format(
                        obj=obj, requires=requires_json))
        elif isinstance(requires_json, dict):
            # Requires designates a whole schema, the enclosing object
            # must match against that schema.
            # Here we resort to a small hack. Proper implementation
            # would require us to validate the parent object from its
            # own context (own list of parent objects). Since doing that
            # and restoring the state would be very complicated we just
            # instantiate a new validator with a subset of our current
            # history here.
            sub_validator = Validator()
            sub_validator._obj_stack = self._obj_stack[:-2]
            sub_validator._validate_no_push(
                Schema(requires_json), parent_obj)


def validate(schema_text, data_text):
    """
    Validate specified JSON text (data_text) with specified schema
    (schema text). Both are converted to JSON objects with
    simplesjon.loads.
    """
    import simplejson as json
    schema = Schema(json.loads(schema_text))
    data = json.loads(data_text)
    return Validator.validate(schema, data)
