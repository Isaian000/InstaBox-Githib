
# Borra los recursos creados para esta actividad: instancia EC2, instancia RDS, bucket S3, secret en Secrets Manager y Security Groups.


set -e

REGION="us-east-1"

EC2_INSTANCE_ID="i-xxxxxxxxxxxxxxxxx"
RDS_INSTANCE_ID="photobooth-db"
S3_BUCKET_NAME="photobooth-xxxxxxx"
SECRET_NAME="photobooth/db-credentials"
EC2_SECURITY_GROUP_ID="sg-xxxxxxxxxxxxxxxxx"
RDS_SECURITY_GROUP_ID="sg-yyyyyyyyyyyyyyyyy"

aws ec2 terminate-instances --instance-ids "$EC2_INSTANCE_ID" --region "$REGION"
aws ec2 wait instance-terminated --instance-ids "$EC2_INSTANCE_ID" --region "$REGION"
echo "EC2 terminada."

aws rds delete-db-instance \
  --db-instance-identifier "$RDS_INSTANCE_ID" \
  --skip-final-snapshot \
  --region "$REGION"
aws rds wait db-instance-deleted --db-instance-identifier "$RDS_INSTANCE_ID" --region "$REGION"
echo "RDS eliminada."

aws s3 rm "s3://$S3_BUCKET_NAME" --recursive --region "$REGION"
aws s3api delete-bucket --bucket "$S3_BUCKET_NAME" --region "$REGION"
echo "Bucket eliminado."

aws secretsmanager delete-secret \
  --secret-id "$SECRET_NAME" \
  --force-delete-without-recovery \
  --region "$REGION"
echo "Secret eliminado."

aws ec2 delete-security-group --group-id "$EC2_SECURITY_GROUP_ID" --region "$REGION" || true
aws ec2 delete-security-group --group-id "$RDS_SECURITY_GROUP_ID" --region "$REGION" || true
echo "Security Groups eliminados."

