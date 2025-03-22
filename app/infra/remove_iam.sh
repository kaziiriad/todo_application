#!/bin/bash
USER=Test_User

# Detach managed policies
for policy in $(aws iam list-attached-user-policies --user-name $USER --query 'AttachedPolicies[*].PolicyArn' --output text); do
  aws iam detach-user-policy --user-name $USER --policy-arn $policy
  echo "Detached policy: $policy"
done

# Delete inline policies
for policy in $(aws iam list-user-policies --user-name $USER --query 'PolicyNames[*]' --output text); do
  aws iam delete-user-policy --user-name $USER --policy-name $policy
  echo "Deleted inline policy: $policy"
done

# Delete access keys
for key in $(aws iam list-access-keys --user-name $USER --query 'AccessKeyMetadata[*].AccessKeyId' --output text); do
  aws iam delete-access-key --user-name $USER --access-key-id $key
  echo "Deleted access key: $key"
done

# Remove from groups
for group in $(aws iam list-groups-for-user --user-name $USER --query 'Groups[*].GroupName' --output text); do
  aws iam remove-user-from-group --user-name $USER --group-name $group
  echo "Removed from group: $group"
done

# Delete login profile (may fail if user doesn't have one - that's OK)
aws iam delete-login-profile --user-name $USER 2>/dev/null
echo "Deleted login profile (if existed)"


# Delete the user
aws iam delete-user --user-name $USER
echo "Deleted user: $USER"