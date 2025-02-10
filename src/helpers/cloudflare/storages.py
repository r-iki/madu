from storages.backends.s3boto3 import S3Boto3Storage    # import S3Boto3Storage


class StaticFilesStorage(S3Boto3Storage):
    # helpers.cloudflare.storages.StaticFilesStorage
    location = 'static'    # lokasi file static

class MediaFilesStorage(S3Boto3Storage):
    #  helpers.cloudflare.storages.MediaFilesStorage
    location = 'media'    # lokasi file media

class ProtectedFileStorages(S3Boto3Storage):
    #  helpers.cloudflare.storages.ProtectedFileStorages
    location = 'protected'    # lokasi file protected