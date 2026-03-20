from hwpx.tools.text_extractor import TextExtractor

with TextExtractor("0001.hwpx") as ex:
    text = ex.extract_text()

print(text)