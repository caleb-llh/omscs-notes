import fitz
doc = fitz.open("syllabus.pdf")
print("Pages:", len(doc))
for i, page in enumerate(doc):
    images = page.get_images()
    print(f"Page {i}: {len(images)} images, {len(page.get_text())} text chars")
