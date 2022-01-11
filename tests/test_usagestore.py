import datetime

from mock import call, patch

import windowsprocessmonitor.usagestore


def test_update():
    store = windowsprocessmonitor.usagestore.UsageStore('some_file')

    start = datetime.datetime(2022, 1, 1)
    end = datetime.datetime(2022, 1, 2, 0, 1)
    with patch.object(store, '_update_day') as patched__update:
        store.update(start.timestamp(), end.timestamp())

    patched__update.assert_has_calls([
        call(datetime.date(2022, 1, 1), 1640991600.0, 1641078000.0),
        call(datetime.date(2022, 1, 2), 1641078000.0, 1641078060.0)
    ])
