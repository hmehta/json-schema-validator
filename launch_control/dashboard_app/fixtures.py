"""
Helper functions for making fixtures that setup specific environment
"""

from contextlib import contextmanager

from django.contrib.auth.models import (User, Group)
from django.core.files.base import ContentFile

from launch_control.dashboard_app.models import (
        Bundle,
        BundleStream,
        )


@contextmanager
def created_bundle_streams(spec):
    """
    Helper context manager that creates bundle streams according to
    specification

    spec is a list of dictionaries with the following keys:
        user: string indicating user name to create [optional]
        group: string indicating group name to create [optional]
        slug: slug-like name [optional]
        name: name of the stream to create [optional]

    yields: list of created bundle streams
    """
    users = set()
    groups = set()
    bundle_streams = []
    for stream_args in spec:
        initargs = {
                'user': None,
                'group': None,
                'slug': stream_args.get('slug', ''),
                'name': stream_args.get('name', '')}
        username = stream_args.get('user')
        if username:
            user = User.objects.get_or_create(username=username)[0]
            users.add(user)
            initargs['user'] = user
        groupname = stream_args.get('group')
        if groupname:
            group = Group.objects.get_or_create(name=groupname)[0]
            groups.add(group)
            initargs['group'] = group
        bundle_stream = BundleStream.objects.create(**initargs)
        bundle_stream.save()
        bundle_streams.append(bundle_stream)
    yield bundle_streams
    for bundle_stream in bundle_streams:
        bundle_stream.delete()
    for user in users:
        user.delete()
    for group in groups:
        group.delete()


@contextmanager
def created_bundles(spec):
    """
    Helper context manager that creates bundles according to specification

    spec is a list of dictionaries with the following keys:
        pathname: string either "/anonymous/" or "/anonymous/SLUG/"
        content: string, text of the bundle
        content_filename: string

    yields: list of created bundles
    """
    bundle_streams = {}
    bundles = []
    # make all bundle streams required  
    for pathname, content_filename, content in spec:
        pathname_parts = pathname.split('/')
        assert len(pathname_parts) == 3 or len(pathname_parts) == 4
        assert pathname_parts[0] == ''
        assert pathname_parts[1] == 'anonymous'
        if len(pathname_parts) == 4:
            # '/anonymous/slug/'.split('/') is ['', 'anonymous', 'slug', '']
            slug = pathname_parts[2]
            assert pathname_parts[3] == ''
        else:
            slug = ''
            assert pathname_parts[2] == ''
        if pathname not in bundle_streams:
            bundle_stream = BundleStream.objects.create(user=None,
                    group=None, slug=slug)
            bundle_stream.save()
            bundle_streams[pathname] = bundle_stream
    # make all bundles
    for pathname, content_filename, content in spec:
        bundle = Bundle.objects.create(
                bundle_stream=bundle_streams[pathname],
                content_filename=content_filename)
        bundle.content.save(content_filename, ContentFile(content))
        bundle.save()
        bundles.append(bundle)
    # give bundles back
    yield bundles
    # clean up
    # Note: We explicitly remove bundles because our @uses_scenarios
    # wrapper does not cope with pristine database configuration Also
    # because of FileFilelds() we need to call delete to get rid of test
    # files in the file system 
    for bundle in bundles:
        bundle.delete()
    for bundle_stream in bundle_streams.itervalues():
        bundle_stream.delete()
