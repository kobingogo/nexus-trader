
import akshare as ak
try:
    print("Fetching THS concepts...")
    df = ak.stock_board_concept_name_ths()
    print("Columns:", df.columns.tolist())
    print("First 5 rows:")
    print(df.head())
    
    # Check if we can find '算力'
    match = df[df['name'].str.contains("算力")]
    if not match.empty:
        print("\nFound '算力' matches:")
        print(match)
        # print first url
        if 'url' in df.columns:
            print("URL example:", match.iloc[0]['url'])
        if 'code' in df.columns:
             print("Code example:", match.iloc[0]['code'])
except Exception as e:
    print(f"Error: {e}")
