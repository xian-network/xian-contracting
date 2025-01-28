#!/bin/bash

# Check if a version bump type was provided
if [ -z "$1" ]; then
    echo "Please provide a version bump type: patch, minor, or major"
    echo "Usage: ./release.sh [patch|minor|major]"
    exit 1
fi

# Validate version bump type
if [ "$1" != "patch" ] && [ "$1" != "minor" ] && [ "$1" != "major" ]; then
    echo "Invalid version bump type. Please use: patch, minor, or major"
    exit 1
fi

# Make sure we're on the master branch
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "master" ]; then
    echo "Please switch to the master branch before creating a release"
    exit 1
fi

# Make sure the working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "Working directory is not clean. Please commit or stash changes first."
    exit 1
fi

# Pull latest changes
echo "Pulling latest changes from master..."
git pull origin master

# Update version using Poetry
echo "Bumping version ($1)..."
poetry version $1
NEW_VERSION=$(poetry version -s)

# Stage and commit version bump
echo "Committing version bump..."
git add pyproject.toml
git commit -m "Bump version to $NEW_VERSION"

# Create and push tag
echo "Creating and pushing tag v$NEW_VERSION..."
git tag "v$NEW_VERSION"
git push && git push --tags

echo "Release process initiated!"
echo "Version $NEW_VERSION will be published to PyPI and GitHub releases automatically."
echo "You can monitor the progress at: https://github.com/xian-network/xian-contracting/actions"