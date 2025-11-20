import logging
from google.cloud import firestore
import random
import time
from secrets import SystemRandom    
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from ..database import db

def update_random_keys_batch():
    collection_ref = db.collection("questions")
    docs = list(collection_ref.stream())
    total = len(docs)
    print(f"Found {total} documents.")

    batch_size = 500
    batch = db.batch()
    count = 0
    updated = 0

    for i, doc in enumerate(docs):
        data = doc.to_dict()

        # ✅ Only update if the document already has a 'randomKey' field
        if "randomKey" in data:
            rand = SystemRandom()  # cryptographically secure generator
            random_key = rand.random()
            logger.info(f"Generated random key for doc {doc.id}: {random_key}")
            batch.update(doc.reference, {"randomKey": random_key})
            count += 1
            updated += 1

            # Commit every 500 updates
            if count % batch_size == 0:
                batch.commit()
                print(f"✅ Committed {updated} updates so far.")
                batch = db.batch()
                time.sleep(0.5)  # avoid rate limit bursts

    # Commit any remaining batch
    if count % batch_size != 0:
        batch.commit()
        print(f"✅ Final commit. Total updated: {updated}")

    print(f"🎉 Done. Updated {updated}/{total} documents that had 'randomKey'.")

if __name__ == "__main__":
    update_random_keys_batch()
