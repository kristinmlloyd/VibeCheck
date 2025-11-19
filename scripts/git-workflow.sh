#!/bin/bash

# Start new feature
new_feature() {
    issue_number=$1
    description=$2
    git checkout develop
    git pull origin develop
    git checkout -b "feature/${issue_number}-${description}"
    echo "✅ Created feature branch: feature/${issue_number}-${description}"
}

# Start bug fix
new_bugfix() {
    issue_number=$1
    description=$2
    git checkout develop
    git pull origin develop
    git checkout -b "bugfix/${issue_number}-${description}"
    echo "✅ Created bugfix branch: bugfix/${issue_number}-${description}"
}

# Update current branch with develop
sync_develop() {
    current_branch=$(git branch --show-current)
    git fetch origin
    git merge origin/develop
    echo "✅ Synced ${current_branch} with develop"
}

# Show usage
case "$1" in
    feature)
        new_feature "$2" "$3"
        ;;
    bugfix)
        new_bugfix "$2" "$3"
        ;;
    sync)
        sync_develop
        ;;
    *)
        echo "Usage:"
        echo "  ./scripts/git-workflow.sh feature <issue-number> <description>"
        echo "  ./scripts/git-workflow.sh bugfix <issue-number> <description>"
        echo "  ./scripts/git-workflow.sh sync"
        ;;
esac