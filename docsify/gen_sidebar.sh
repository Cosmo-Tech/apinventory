#!/bin/sh

# This script has been generated from Gemini 3
# It creates a Docsify sidebar distributed in Nginx (the goal is to run this script at Nginx Docker container start).

DIR="/usr/share/nginx/html/files"
SIDEBAR="$DIR/_sidebar.md"
README="$DIR/README.md"

echo "starting sidebar generation"

cat "$SIDEBAR" > "$README"
cd "$DIR" || exit

find . -type f -name "*.md" | grep -v "_sidebar.md" | grep -v "^\./README.md" | sort | awk -F/ '
BEGIN {
    print "* [Cosmo Tech platforms inventory](/)"
}
    sub(/^\.\//, "", $0)
    path = ""
    indent = ""

    for (i = 1; i <= NF; i++) {
        name = $i
        if (path == "")
            path = name
        else
            path = path "/" name

        indent = ""
        for (j = 1; j < i; j++) {
            indent = indent "  "
        }

        if (i == NF) {
            display_name = name
            sub(/\.md$/, "", display_name)

            print indent "* [" display_name "](" path ")"
        }
        else {
            if (!seen[path]++) {
                print indent "* " name
            }
        }
    }
}' > "$SIDEBAR"


chmod -R 755 "$DIR"

echo "sidebar generated"
echo "starting Nginx..."

# Kill nginx after given time, so the container will restart with :alaways in docker-compose.yaml, and then the sidebar will be regenerated (this is a trick to always have an up-to-date inventory)
timeout 600 nginx -g "daemon off;"