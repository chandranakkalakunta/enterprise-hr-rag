#!/usr/bin/env python3
"""
HR Data Loader - ChandraAILabs HR RAG Platform
Creates schema and loads sample employee data
"""
import argparse
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True)
    parser.add_argument('--instance', required=True)
    parser.add_argument('--db', required=True)
    parser.add_argument('--user', required=True)
    parser.add_argument('--password', required=True)
    parser.add_argument('--region', default='asia-south1')
    args = parser.parse_args()

    sys.path.insert(0, 'src/database')
    from hr_db_client import HRDBClient

    client = HRDBClient(
        project_id=args.project,
        instance_name=args.instance,
        db_name=args.db,
        db_user=args.user,
        db_password=args.password,
        region=args.region
    )

    print("Creating schema...")
    client.create_schema()
    print("Schema created!")

    print("Loading sample data...")
    client.load_sample_data()
    print("Data loaded!")

    print("Verifying...")
    stats = client.get_stats()
    for table, count in stats.items():
        print(f"  {table}: {count} rows")

    print("Done!")

if __name__ == "__main__":
    main()
