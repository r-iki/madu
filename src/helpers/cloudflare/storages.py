from storages.backends.s3boto3 import S3Boto3Storage    # import S3Boto3Storage


class StaticFilesStorage(S3Boto3Storage):
    # helpers.cloudflare.storages.StaticFilesStorage
    location = 'static'    # lokasi file static
    custom_domain = 'static.madu.software'   # domain custom

class MediaFilesStorage(S3Boto3Storage):
    #  helpers.cloudflare.storages.MediaFilesStorage
    location = 'media'    # lokasi file media
    custom_domain = 'media.madu.software'    # domain custom
    

class ProtectedFileStorages(S3Boto3Storage):
    #  helpers.cloudflare.storages.ProtectedFileStorages
    location = 'protected'    # lokasi file protected