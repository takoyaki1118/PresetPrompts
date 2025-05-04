# PresetPrompts/preset_prompt.py
import os
import json
import random
import re
import traceback

# --- Helper Function ---
def _parse_specific_choices(choices_str):
    """Helper function to parse comma or newline separated strings into a list."""
    if not choices_str or not choices_str.strip():
        return []
    items = re.split(r'\s*,\s*|\s*\n\s*', choices_str.strip())
    return [item.strip() for item in items if item.strip()]

# --- Load Preset Data ---
PRESETS = {}
PRESET_FILE_PATH = os.path.join(os.path.dirname(__file__), 'presets.json')

try:
    if os.path.exists(PRESET_FILE_PATH):
        with open(PRESET_FILE_PATH, 'r', encoding='utf-8') as f:
            PRESETS = json.load(f)
            if "None" not in PRESETS:
                 PRESETS["None"] = {"_description": "Fallback None preset"}
            print(f"[PresetPrompts] Loaded {len(PRESETS)} presets from {PRESET_FILE_PATH}")
    else:
        print(f"[PresetPrompts] Warning: Preset file not found at {PRESET_FILE_PATH}. Creating default 'None' preset.")
        PRESETS = {"None": {"_description": "Default None preset"}}
except json.JSONDecodeError as e:
    print(f"[PresetPrompts] Error loading presets.json: {e}")
    print(f"[PresetPrompts] Please check the JSON syntax in {PRESET_FILE_PATH}")
    traceback.print_exc()
    PRESETS = {"None": {"_description": "Error Loading Presets"}}
except Exception as e:
    print(f"[PresetPrompts] An unexpected error occurred loading presets: {e}")
    traceback.print_exc()
    PRESETS = {"None": {"_description": "Error Loading Presets"}}


# --- Node Class Definition ---
class PresetPromptGenerator:
    CATEGORY = "PresetPrompts"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "generate_preset_prompt"

    # Define the order AND the categories that can be toggled
    PRESET_CATEGORY_ORDER = [
        "keywords", "character_details", "clothing", "accessories",
        "pose", "expression", "lighting", "background"
    ]

    @classmethod
    def INPUT_TYPES(cls):
        preset_names = list(PRESETS.keys())
        if not preset_names:
            preset_names = ["None"]

        required = {
            "preset_name": (preset_names,),
            "prefix_tags": ("STRING", {"multiline": True, "default": "masterpiece, best quality"}),
            "character": ("STRING", {"multiline": False, "default": ""}),
            "suffix_tags": ("STRING", {"multiline": True, "default": ""}),
            "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
        }

        # --- Add category toggle inputs ---
        for category in cls.PRESET_CATEGORY_ORDER:
            input_name = f"enable_{category}"
            # Add category toggle with default True (enabled)
            required[input_name] = ("BOOLEAN", {"default": True})
            # You could also place these in "optional" if preferred

        return {"required": required} # Return combined inputs

    # **** IMPORTANT: Add all the new boolean flags to the function signature ****
    def generate_preset_prompt(self, preset_name, prefix_tags, character, suffix_tags, seed,
                               # Add arguments matching the new inputs
                               enable_keywords, enable_character_details, enable_clothing,
                               enable_accessories, enable_pose, enable_expression,
                               enable_lighting, enable_background): # Ensure all categories from PRESET_CATEGORY_ORDER are listed here

        rng = random.Random(seed)
        prompt_parts = []

        # Create a mapping from category name to its enable flag for easy lookup
        enable_flags = {
            "keywords": enable_keywords,
            "character_details": enable_character_details,
            "clothing": enable_clothing,
            "accessories": enable_accessories,
            "pose": enable_pose,
            "expression": enable_expression,
            "lighting": enable_lighting,
            "background": enable_background,
        }

        # 1. Add Prefix Tags
        prompt_parts.extend(_parse_specific_choices(prefix_tags))

        # 2. Add Character (if specified)
        if character and character.strip():
            prompt_parts.extend(_parse_specific_choices(character))

        # 3. Process Selected Preset
        selected_preset_data = PRESETS.get(preset_name)

        if selected_preset_data and preset_name != "None":
            # Iterate through categories in defined order
            for category in self.PRESET_CATEGORY_ORDER:
                # **** Check if this category is enabled ****
                if enable_flags.get(category, False): # Check the flag (default to False if somehow missing)
                    tag_options = selected_preset_data.get(category, [])
                    if isinstance(tag_options, list) and tag_options:
                        chosen_tag = rng.choice(tag_options)
                        if chosen_tag and chosen_tag.strip():
                             prompt_parts.append(chosen_tag.strip())

        # 4. Add Suffix Tags
        prompt_parts.extend(_parse_specific_choices(suffix_tags))

        # 5. Combine and Clean
        ordered_unique_parts = []
        seen = set()
        for part in prompt_parts:
             stripped_part = part.strip()
             if stripped_part and stripped_part not in seen:
                  ordered_unique_parts.append(stripped_part)
                  seen.add(stripped_part)

        final_prompt = ", ".join(filter(None, ordered_unique_parts))
        final_prompt = re.sub(r'(,\s*){2,}', ', ', final_prompt)
        final_prompt = re.sub(r'^\s*,\s*|\s*,\s*$', '', final_prompt)

        return (final_prompt,)

# Make sure __init__.py correctly imports this class and defines mappings