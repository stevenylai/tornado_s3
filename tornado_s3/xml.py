"""Convert AWS S3 XML response to JSON"""
from xml.etree import ElementTree


def _walk_etree(element, result, prune=True):
    """walk etree and save result to dict"""
    text = element.text
    if text is not None and len(text.strip()) > 0:
        result['text'] = text.strip()
    for child in element:
        next_level = None
        tag = child.tag.split('}', 1)[1]
        if tag not in result:
            result[tag] = {}
            next_level = result[tag]
        else:
            if isinstance(result[tag], list):
                result[tag].append({})
            else:
                result[tag] = [result[tag], {}]
            next_level = result[tag][-1]
        _walk_etree(child, next_level, prune)
        if prune and isinstance(
                result[tag], dict
        ) and len(result[tag]) == 1 and 'text' in result[tag]:
            result[tag] = next_level['text']


def to_json(xml_data):
    """Convert to JSON
    >>> data = '''
    ... <ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
    ...   <Name>example-bucket</Name>
    ...   <Prefix></Prefix>
    ...   <Marker></Marker>
    ...   <MaxKeys>1000</MaxKeys>
    ...   <Delimiter>/</Delimiter>
    ...   <IsTruncated>false</IsTruncated>
    ...   <Contents>
    ...     <Key>sample.jpg</Key>
    ...     <LastModified>2011-02-26T01:56:20.000Z</LastModified>
    ...     <ETag>&quot;bf1d737a4d46a19f3bced6905cc8b902&quot;</ETag>
    ...     <Size>142863</Size>
    ...     <Owner>
    ...       <ID>canonical-user-id</ID>
    ...       <DisplayName>display-name</DisplayName>
    ...     </Owner>
    ...     <StorageClass>STANDARD</StorageClass>
    ...   </Contents>
    ...   <CommonPrefixes>
    ...     <Prefix>photos/</Prefix>
    ...   </CommonPrefixes>
    ... </ListBucketResult>
    ... '''
    >>> import json
    >>> to_json(data) == {
    ...   "MaxKeys": "1000",
    ...   "Prefix": {},
    ...   "Marker": {},
    ...   "Contents": {
    ...     "StorageClass": "STANDARD",
    ...     "Size": "142863",
    ...     "ETag": '"bf1d737a4d46a19f3bced6905cc8b902"',
    ...     "Owner": {
    ...       "ID": "canonical-user-id",
    ...       "DisplayName": "display-name"
    ...     },
    ...     "LastModified": "2011-02-26T01:56:20.000Z",
    ...     "Key": "sample.jpg"
    ...   },
    ...   "Name": "example-bucket",
    ...   "CommonPrefixes": {
    ...     "Prefix": "photos/"
    ...   },
    ...   "Delimiter": "/",
    ...   "IsTruncated": "false"
    ... }
    True
    """
    root = ElementTree.fromstring(xml_data)
    result = {}
    _walk_etree(root, result)
    return result


if __name__ == '__main__':
    import doctest
    doctest.testmod()
