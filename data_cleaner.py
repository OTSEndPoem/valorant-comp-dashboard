import pandas as pd
from dateutil import parser

def clean_scrim_form(path):
    """
    Cleans scrim tracking sheets with date-labeled section headers
    and blocks of match data. Assumes headers are already present.
    """
    if path.endswith('.xlsx'):
        raw_df = pd.read_excel(path)
    else:
        raw_df = pd.read_csv(path)

    raw_rows = raw_df.values.tolist()
    cleaned_rows = []
    current_date = None

    def is_date_string(value):
        try:
            parser.parse(str(value), fuzzy=True)
            return True
        except:
            return False

    for i, row in enumerate(raw_rows):
        first_cell = str(row[0]).strip()

        # Identify date separator row
        if is_date_string(first_cell) and all(pd.isna(cell) or cell == '' for cell in row[1:]):
            current_date = parser.parse(first_cell, fuzzy=True).strftime('%Y-%m-%d')
            print(f"📅 Detected date '{first_cell}' as {current_date} at row {i}")
            continue

        # Match row (at least team name + map + side must be present)
        if current_date and pd.notna(row[0]) and pd.notna(row[1]) and pd.notna(row[2]):
            cleaned_rows.append([current_date] + row)
        else:
            print(f"⚠️ Skipping row {i}: missing date or core values -> {row[:5]}")

    if not cleaned_rows:
        raise ValueError("❌ No valid matches found in file")

    columns = ['Date'] + raw_df.columns.tolist()
    return pd.DataFrame(cleaned_rows, columns=columns)

# Run this when executed directly
if __name__ == "__main__":
    df = clean_scrim_form("score.csv")
    print(f"✅ Cleaned {len(df)} matches:")
    print(df.head(10))
    print(f"📊 Total matches (based on outcomes): {df['Outcome'].notna().sum()}")
    df.to_csv("cleaned_score.csv", index=False)
    print("📁 Saved to cleaned_score.csv")
