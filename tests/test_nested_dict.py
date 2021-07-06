from nested_dict import __version__, NestedDict

EMPTY_NESTED_DICT = NestedDict()


def test_version():
    assert __version__ == '0.1.0'


def test__getitem__():
    document = {
        "products": {
            "EndpointSecure": {
                "max_devices": 5
                }
            }
        }
    bad_account = NestedDict(document)
    assert bad_account['products'] == {
        "EndpointSecure": {
            "max_devices": 5
            }
        }

    assert bad_account['products']['EndpointSecure'] == {"max_devices": 5}
    assert bad_account['products']['EndpointSecure']["max_devices"] == 5
    assert bad_account['bad'] == EMPTY_NESTED_DICT
    assert bad_account['bad']['worse'] == EMPTY_NESTED_DICT
    assert bad_account['bad']['worse'] == EMPTY_NESTED_DICT
    assert bad_account['products']['bad'] == EMPTY_NESTED_DICT
    assert bad_account['products']['bad']['worse'] == EMPTY_NESTED_DICT
    assert bad_account['products']['EndpointSecure']['bad'] == EMPTY_NESTED_DICT
    assert bad_account['products']['EndpointSecure']['bad']['worse'] == EMPTY_NESTED_DICT


def test__setitem__shallow():
    document = {
        "products": {
            "EndpointSecure": {
                "max_devices": 5
                }
            }
        }
    bad_account = NestedDict(document)
    bad_account['string'] = 'value'
    bad_account['dict'] = {'key': 'value'}
    test__getitem__()
    assert bad_account['string'] == 'value'
    assert bad_account['dict'] == {'key': 'value'}
    assert bad_account['dict']['key'] == 'value'
    assert bad_account['dict']['bad'] == EMPTY_NESTED_DICT
    assert bad_account['dict']['bad']['worse'] == EMPTY_NESTED_DICT


def test__setitem__nested():
    document = {
        "products": {
            "EndpointSecure": {
                "max_devices": 5
                }
            }
        }
    bad_account = NestedDict(document)
    bad_account['bad']['worse'] = {'worsekey': 'worsevalue'}
    assert bad_account['bad'] == {'worse': {'worsekey': 'worsevalue'}}
    assert bad_account['bad']['worse'] == {'worsekey': 'worsevalue'}
    print(f'bad_account: {repr(bad_account)}')
