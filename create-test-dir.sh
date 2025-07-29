#!/bin/bash

# Delete existing test directory if it exists
if [ -d "test_dir" ]; then
    rm -rf test_dir
fi

# Create test directory
mkdir test_dir

# Make episodes
touch "test_dir/Episode 1 - My First Episode.mkv"
touch "test_dir/Episode 2 - My Second Episode.mkv"
touch "test_dir/Episode 3 - My Third Episode.mkv"
touch "test_dir/Episode 4 - My Fourth Episode.mkv"
touch "test_dir/Episode 5 - My Fifth Episode.mkv"
touch "test_dir/Episode 6 - My Sixth Episode.mkv"
touch "test_dir/Episode 7 - My Seventh Episode.mkv"
touch "test_dir/Episode 8 - My Eighth Episode.mkv"
touch "test_dir/Episode 9 - My Ninth Episode.mkv"
touch "test_dir/Episode 10 - My Tenth Episode.mkv"

# Make sample anifix.spec file
cat <<EOL > test_dir/anifix.spec
# Season | Episode range
1 | 1-4
2 | 5-7
3 | 8-10
EOL

# Confirmation message
echo "Test directory 'test_dir' created with sample episodes and anifix.spec file."
