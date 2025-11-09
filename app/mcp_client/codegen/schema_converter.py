"""JSON Schema to Pydantic model converter for code generation."""

from typing import Any, Dict, Set, List


class SchemaConverter:
    """
    Converts JSON Schema to Pydantic model code.
    
    Supports common JSON Schema types and generates Python/Pydantic
    compatible code with proper type hints and Field annotations.
    """
    
    def __init__(self):
        """Initialize the schema converter."""
        self.python_keywords = {
            'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue',
            'def', 'del', 'elif', 'else', 'except', 'False', 'finally', 'for',
            'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None',
            'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'True', 'try',
            'while', 'with', 'yield', 'list', 'dict', 'set', 'type'
        }
    
    def json_schema_to_pydantic(
        self,
        schema: Dict[str, Any],
        model_name: str,
        description: str = None
    ) -> str:
        """
        Convert JSON Schema to Pydantic model code.
        
        Args:
            schema: JSON Schema dictionary
            model_name: Name for the generated Pydantic model
            description: Optional description for the model
            
        Returns:
            Python code string for Pydantic model
        """
        properties = schema.get("properties", {})
        required_fields = set(schema.get("required", []))
        
        lines = []
        
        # Class definition
        lines.append(f"class {model_name}(BaseModel):")
        
        # Docstring
        if description:
            lines.append(f'    """{description}"""')
        else:
            lines.append(f'    """Auto-generated Pydantic model from JSON Schema."""')
        lines.append("")
        
        # Generate fields
        if not properties:
            lines.append("    pass")
        else:
            for prop_name, prop_schema in properties.items():
                field_code = self._generate_field(
                    prop_name,
                    prop_schema,
                    is_required=prop_name in required_fields
                )
                lines.append(f"    {field_code}")
        
        return "\n".join(lines)
    
    def _generate_field(
        self,
        field_name: str,
        schema: Dict[str, Any],
        is_required: bool
    ) -> str:
        """
        Generate code for a single field.
        
        Args:
            field_name: Name of the field
            schema: JSON Schema for the field
            is_required: Whether field is required
            
        Returns:
            Python code for field definition
        """
        # Sanitize field name
        safe_name = self._sanitize_name(field_name)
        
        # Get Python type
        python_type = self._map_type(schema, is_required)
        
        # Get description
        description = schema.get("description", "")
        
        # Generate Field() annotation if needed
        field_kwargs = []
        
        if safe_name != field_name:
            field_kwargs.append(f'alias="{field_name}"')
        
        if description:
            field_kwargs.append(f'description="{description}"')
        
        if "default" in schema:
            default_val = repr(schema["default"])
            field_kwargs.append(f'default={default_val}')
        elif not is_required:
            field_kwargs.append('default=None')
        
        # Build field definition
        if field_kwargs:
            field_str = f"Field({', '.join(field_kwargs)})"
        elif not is_required:
            field_str = "None"
        else:
            field_str = None
        
        # Combine type and field
        if field_str:
            return f"{safe_name}: {python_type} = {field_str}"
        else:
            return f"{safe_name}: {python_type}"
    
    def _map_type(self, schema: Dict[str, Any], is_required: bool) -> str:
        """
        Map JSON Schema type to Python type.
        
        Args:
            schema: JSON Schema for the field
            is_required: Whether field is required
            
        Returns:
            Python type string
        """
        json_type = schema.get("type")
        
        # Handle enum (Literal type)
        if "enum" in schema:
            enum_values = ', '.join(repr(v) for v in schema["enum"])
            base_type = f"Literal[{enum_values}]"
        # Handle array
        elif json_type == "array":
            items_schema = schema.get("items", {})
            item_type = self._map_type(items_schema, True)
            base_type = f"List[{item_type}]"
        # Handle object (dict)
        elif json_type == "object":
            # Check for additionalProperties
            if "additionalProperties" in schema:
                value_type = self._map_type(
                    schema["additionalProperties"],
                    True
                )
                base_type = f"Dict[str, {value_type}]"
            else:
                base_type = "Dict[str, Any]"
        # Handle union types
        elif isinstance(json_type, list):
            types = [self._simple_type_map(t) for t in json_type if t != "null"]
            if len(types) == 1:
                base_type = types[0]
            else:
                base_type = f"Union[{', '.join(types)}]"
        # Handle simple types
        else:
            base_type = self._simple_type_map(json_type)
        
        # Wrap in Optional if not required
        if not is_required and not base_type.startswith("Optional"):
            return f"Optional[{base_type}]"
        
        return base_type
    
    def _simple_type_map(self, json_type: str) -> str:
        """
        Map simple JSON types to Python types.
        
        Args:
            json_type: JSON Schema type string
            
        Returns:
            Python type string
        """
        mapping = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "array": "List[Any]",
            "object": "Dict[str, Any]",
            "null": "None"
        }
        return mapping.get(json_type, "Any")
    
    def _sanitize_name(self, name: str) -> str:
        """
        Sanitize field name for Python identifier.
        
        Args:
            name: Original field name
            
        Returns:
            Valid Python identifier
        """
        # Replace invalid characters
        safe_name = name.replace("-", "_").replace(".", "_").replace(" ", "_")
        
        # Handle Python keywords
        if safe_name in self.python_keywords:
            safe_name = f"{safe_name}_"
        
        # Ensure doesn't start with number
        if safe_name and safe_name[0].isdigit():
            safe_name = f"field_{safe_name}"
        
        return safe_name
