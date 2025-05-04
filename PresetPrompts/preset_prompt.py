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
    # Normalize separators to commas, handle potential spaces around commas/newlines
    items = re.split(r'\s*,\s*|\s*\n\s*', choices_str.strip())
    # Filter out empty elements
    return [item.strip() for item in items if item.strip()]

# --- Load Preset Data ---
PRESETS = {}
PRESET_FILE_PATH = os.path.join(os.path.dirname(__file__), 'presets.json')

try:
    if os.path.exists(PRESET_FILE_PATH):
        with open(PRESET_FILE_PATH, 'r', encoding='utf-8') as f:
            PRESETS = json.load(f)
            # Ensure "None" preset exists if not defined in the file
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
    PRESETS = {"None": {"_description": "Error Loading Presets"}} # Fallback
except Exception as e:
    print(f"[PresetPrompts] An unexpected error occurred loading presets: {e}")
    traceback.print_exc()
    PRESETS = {"None": {"_description": "Error Loading Presets"}} # Fallback


# --- Node Class Definition ---
class PresetPromptGenerator:
    CATEGORY = "PresetPrompts" # Separate category for this node
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "generate_preset_prompt"

    # Define the order in which preset categories should be potentially added.
    # This helps maintain some structure in the output prompt.
    PRESET_CATEGORY_ORDER = [
        "keywords", "character_details", "clothing", "accessories",
        "pose", "expression", "lighting", "background"
    ]

    @classmethod
    def INPUT_TYPES(cls):
        preset_names = list(PRESETS.keys())
        if not preset_names: # Ensure there's at least a 'None' option
            preset_names = ["None"]

        return {
            "required": {
                "preset_name": (preset_names,), # Create dropdown from loaded preset names
                "prefix_tags": ("STRING", {"multiline": True, "default": "masterpiece, best quality"}),
                # Allow specifying a character, separate from preset details
                "character": ("STRING", {"multiline": False, "default": ""}),
                "suffix_tags": ("STRING", {"multiline": True, "default": ""}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }

    def generate_preset_prompt(self, preset_name, prefix_tags, character, suffix_tags, seed):
        rng = random.Random(seed)
        prompt_parts = []

        # 1. Add Prefix Tags
        prompt_parts.extend(_parse_specific_choices(prefix_tags))

        # 2. Add Character (if specified)
        if character and character.strip():
            # Treat as potentially multiple tags for flexibility
            prompt_parts.extend(_parse_specific_choices(character))
            # If you want character to always be a single block:
            # prompt_parts.append(character.strip())

        # 3. Process Selected Preset
        selected_preset_data = PRESETS.get(preset_name)

        if selected_preset_data and preset_name != "None":
            # Iterate through categories in a defined order for consistency
            for category in self.PRESET_CATEGORY_ORDER:
                tag_options = selected_preset_data.get(category, [])
                if isinstance(tag_options, list) and tag_options: # Check if it's a non-empty list
                    # Choose one randomly from the list
                    chosen_tag = rng.choice(tag_options)
                    if chosen_tag and chosen_tag.strip(): # Ensure the chosen tag isn't empty
                         prompt_parts.append(chosen_tag.strip())

        # 4. Add Suffix Tags
        prompt_parts.extend(_parse_specific_choices(suffix_tags))

        # 5. Combine and Clean
        # Remove potential duplicates while preserving order (simple approach)
        ordered_unique_parts = []
        seen = set()
        for part in prompt_parts:
            # Strip before checking to handle duplicates differing only by whitespace
             stripped_part = part.strip()
             if stripped_part and stripped_part not in seen:
                  ordered_unique_parts.append(stripped_part)
                  seen.add(stripped_part)

        final_prompt = ", ".join(filter(None, ordered_unique_parts)) # filter(None, ...) removes empty strings

        # Clean up potential double commas or leading/trailing commas
        final_prompt = re.sub(r'(,\s*){2,}', ', ', final_prompt) # Replace multiple commas with one
        final_prompt = re.sub(r'^\s*,\s*|\s*,\s*$', '', final_prompt) # Trim leading/trailing commas

        return (final_prompt,)