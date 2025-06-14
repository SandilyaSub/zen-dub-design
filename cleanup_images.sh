#!/bin/bash

# Keep the 3 most recent images and delete the rest
# Get all images sorted by creation time (newest first)
IMAGES=$(gcloud artifacts docker images list asia-south1-docker.pkg.dev/phonic-bivouac-272213/cloud-run-source-deploy/indic-translator --sort-by=~CREATE_TIME --format="value(DIGEST)")

# Convert to array
IFS=$'\n' read -d '' -r -a IMAGE_ARRAY <<< "$IMAGES"

# Keep count of how many images we've seen
COUNT=0

# Loop through images
for digest in "${IMAGE_ARRAY[@]}"; do
  COUNT=$((COUNT+1))
  
  # Skip the first 3 images (the most recent ones)
  if [ $COUNT -le 3 ]; then
    echo "Keeping image with digest: $digest"
  else
    echo "Deleting image with digest: $digest"
    gcloud artifacts docker images delete asia-south1-docker.pkg.dev/phonic-bivouac-272213/cloud-run-source-deploy/indic-translator@$digest --quiet
  fi
done
