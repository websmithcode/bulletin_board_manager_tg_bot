from operator import itemgetter as iget
import json
from typing import Union


chars = "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯABCDEFGHIJKLMNOPQRSTUVWXYZ"

tags = """{
    "4": {
      "tag": "#\u043c\u0430\u0440\u043a\u0435\u0442\u0438\u043d\u0433"
    },
    "6": {
      "tag": "#\u043a\u0440\u0438\u043f\u0442\u043e\u0432\u0430\u043b\u044e\u0442\u044b"
    },
    "7": {
      "tag": "#\u0432\u0430\u043a\u0430\u043d\u0441\u0438\u0438"
    },
    "8": {
      "tag": "#\u0434\u0438\u0437\u0430\u0439\u043d"
    },
    "9": {
      "tag": "#\u043c\u0435\u0431\u0435\u043b\u044c"
    },
    "10": {
      "tag": "#\u043f\u0441\u0438\u0445\u043e\u043b\u043e\u0433"
    },
    "11": {
      "tag": "#\u0440\u0430\u0441\u0441\u044b\u043b\u043a\u0438"
    },
    "12": {
      "tag": "#\u0442\u0435\u043b\u0435\u0433\u0440\u0430\u043c"
    }
  }"""

tags = set(map(iget('tag'), json.loads(tags).values()))


def split_by_chunks(val: str, size: int, out_type="list") -> Union[list, str]:
    """Split string by chunks"""
    chunks = [list(val[i:i+size]) for i in range(0, len(val), size)]
    match out_type:
        case "list":
            return chunks
        case "str":
            return list(map(lambda x: f'{x[0]}-{x[-1]}' if len(x) > 1 else x[0], chunks))
        case _:
            raise ValueError("Unknown out_type")


def get_letters_of_tags(tags_list: list, upper=True) -> list:
    """Get letters of tags"""
    letters = list(sorted(set(map(lambda tag: tag.strip('#')[0], tags_list))))
    if upper:
        letters = list(map(str.upper, letters))
    return letters


letters = get_letters_of_tags(tags)

# letters = set(map(
#     lambda x: x.get('tag').strip('#')[0].upper(),
#     json.loads(tags).values()))

# print(letters)
print(split_by_chunks(list(letters), 4, "str"))
