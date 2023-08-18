from enum import Enum


def get_string_and_remove_enum_flags(text: str, enum_type: Enum) -> tuple[list[str], str]:
  matches = []
  new_text = text
  
  for value in enum_type:
    if value.value in text:
      new_text = new_text.replace(value.value, '', 1)
      matches.append(value) 

  return matches, new_text