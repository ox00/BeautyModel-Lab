import os
import sys
import json
import argparse

# Add project root to path to allow importing from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.loaders.csv_loader import BatchLoader

def view_data(table_name: str, row_index: int = 0):
    data_path = os.path.join(project_root, "data/deliveries/2026-03-14-baseline-v1/p0")
    
    try:
        # 1. 加载数据到内存
        bundle = BatchLoader.load_batch(data_path)
    except Exception as e:
        print(f"❌ Failed to load data: {e}")
        return

    print(f"Batch version: {bundle.batch_version}")
    print(f"Batch timestamp: {bundle.batch_timestamp}")
    if bundle.warnings:
        for warning in bundle.warnings:
            print(f"Warning: {warning}")

    # 2. 检查表名是否存在
    if table_name not in bundle.data:
        print(f"❌ Table '{table_name}' not found.")
        print(f"Available tables: {', '.join(bundle.data.keys())}")
        return

    df = bundle.data[table_name]
    
    # 3. 检查行号是否越界
    if row_index < 0 or row_index >= len(df):
        print(f"❌ Row index {row_index} out of bounds. The '{table_name}' table has {len(df)} rows (0 to {len(df)-1}).")
        return

    # 4. 提取那一行数据并转换为字典
    row_dict = df.iloc[row_index].to_dict()

    # 5. 使用 Schema 模型进行格式化，这能展示数据在 Pydantic 中真实的样子
    schema_cls = BatchLoader.SCHEMA_MAP[table_name]
    try:
        validated_obj = schema_cls(**row_dict)
        # 将 Pydantic 对象转为 JSON 字符串打印，忽略为 None 的空字段，使其更清爽
        output_json = validated_obj.model_dump_json(indent=2, exclude_none=True)
        print(f"\n=== Memory View: {table_name} [Row {row_index}] ===")
        print(output_json)
        print("==================================================\n")
    except Exception as e:
        print(f"❌ Failed to validate row against schema: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View a specific row of data from the loaded memory bundle.")
    parser.add_argument("table", type=str, help="Name of the table (e.g., trend_signal, compliance_rule)")
    parser.add_argument("--row", type=int, default=0, help="Row index to view (default is 0)")
    
    args = parser.parse_args()
    view_data(args.table, args.row)
