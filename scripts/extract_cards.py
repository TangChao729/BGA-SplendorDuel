import pdfplumber, json

def parse_table(table, level):
    hdr = table[1]
    # locate each column by header name:
    idx = {name: hdr.index(name) for name in (
        "Color","Points","Bonus","Ability","Crowns",
        "Cost Pearl","Cost Black","Cost Red",
        "Cost Green","Cost Blue","Cost White"
    )}
    cards = []
    for row in table[2:]:
        color = row[idx["Color"]]
        # Points: blank→level (only blanks on level 1)
        pts = row[idx["Points"]].strip()
        points = int(pts) if pts else 0
        bonus = int(row[idx["Bonus"]]) if row[idx["Bonus"]].strip().isdigit() else 0
        ability = row[idx["Ability"]].strip() or None
        crowns  = int(row[idx["Crowns"]]) if row[idx["Crowns"]].strip().isdigit() else 0
        def cost(col): 
            v = row[idx[col]].strip()
            return int(v) if v.isdigit() else 0
        cost = {
            "pearl": cost("Cost Pearl"),
            "black": cost("Cost Black"),
            "red":   cost("Cost Red"),
            "green": cost("Cost Green"),
            "blue":  cost("Cost Blue"),
            "white": cost("Cost White"),
        }
        cards.append({
            "level":   level,
            "color":   color,
            "points":  points,
            "bonus":   bonus,
            "ability": ability,
            "crowns":  crowns,
            "cost":    cost
        })
    return cards

with pdfplumber.open("Splendor_Duel_Card_List-v3.pdf") as pdf:
    table = pdf.pages[0].extract_tables()[0]
    table[1][10] = 'Cost White'  # fix header name
    lvl1 = parse_table(table, 1)
    lvl2 = parse_table(pdf.pages[1].extract_tables()[0], 2)
    lvl3 = parse_table(pdf.pages[1].extract_tables()[1], 3)

# assign ids
for lvl, cards in enumerate((lvl1, lvl2, lvl3), start=1):
    for i, c in enumerate(cards, start=1):
        c["id"] = f"{lvl}-{i:02d}"

out = {"level_1": lvl1, "level_2": lvl2, "level_3": lvl3}

with open("cards.json", "w") as f:
    json.dump(out, f, indent=2)