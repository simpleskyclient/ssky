import pytest
from ssky.post import shorten_url


class TestUrlShortening:
    """Test URL shortening functionality."""

    def test_shorten_url_no_path(self):
        """Test URL with no path."""
        url = "https://example.com"
        assert shorten_url(url) == "example.com"

    def test_shorten_url_root_path(self):
        """Test URL with root path only."""
        url = "https://example.com/"
        assert shorten_url(url) == "example.com"

    def test_shorten_url_single_path_component(self):
        """Test URL with single path component (no directory)."""
        url = "https://example.com/path"
        assert shorten_url(url) == "example.com/path"

        url = "https://example.com/verylongfilename.html"
        assert shorten_url(url) == "example.com/verylongfilename.html"

    def test_shorten_url_one_directory_short_filename(self):
        """Test URL with one directory and short filename (3 chars or less)."""
        url = "https://example.com/dir/abc"
        assert shorten_url(url) == "example.com/dir/abc"

        url = "https://example.com/directory/a"
        assert shorten_url(url) == "example.com/directory/a"

    def test_shorten_url_one_directory_long_filename(self):
        """Test URL with one directory and long filename (more than 3 chars)."""
        url = "https://example.com/dir/file.html"
        assert shorten_url(url) == "example.com/dir/fil..."

        url = "https://example.com/dir/verylongfilename.html"
        assert shorten_url(url) == "example.com/dir/ver..."

    def test_shorten_url_multiple_directories_short_parts(self):
        """Test URL with multiple directories where 2nd directory is short (3 chars or less)."""
        url = "https://example.com/dir/sub/abc"
        assert shorten_url(url) == "example.com/dir/sub..."

        url = "https://example.com/directory/a/b/c"
        assert shorten_url(url) == "example.com/directory/a..."

    def test_shorten_url_multiple_directories_long_parts(self):
        """Test URL with multiple directories where 2nd directory is long (more than 3 chars)."""
        url = "https://example.com/dir/subdir/file"
        assert shorten_url(url) == "example.com/dir/sub..."

        url = "https://example.com/directory/subdirectory/filename.html"
        assert shorten_url(url) == "example.com/directory/sub..."

    def test_shorten_url_multiple_directories_mixed_lengths(self):
        """Test URL with multiple directories with mixed lengths."""
        url = "https://example.com/dir/abc/verylongname.html"
        assert shorten_url(url) == "example.com/dir/abc..."

        url = "https://example.com/directory/subdir/ab/file"
        assert shorten_url(url) == "example.com/directory/sub..."

    def test_shorten_url_http_scheme(self):
        """Test URL with http scheme (should also be removed)."""
        url = "http://example.com/dir/file.html"
        assert shorten_url(url) == "example.com/dir/fil..."

    def test_shorten_url_complex_real_world(self):
        """Test with real-world complex URLs."""
        url = "https://github.com/simpleskyclient/ssky"
        assert shorten_url(url) == "github.com/simpleskyclient/ssk..."

        url = "https://docs.python.org/3/library/urllib.parse.html"
        assert shorten_url(url) == "docs.python.org/3/lib..."

        url = "https://www.example.com/products/item123"
        assert shorten_url(url) == "www.example.com/products/ite..."

    def test_shorten_url_preserves_authority(self):
        """Test that authority (domain) is always preserved."""
        url = "https://very-long-subdomain.example.com/path"
        assert shorten_url(url) == "very-long-subdomain.example.com/path"

    def test_shorten_url_three_char_boundary(self):
        """Test the 3-character boundary condition."""
        # Exactly 3 chars - should not be shortened
        url = "https://example.com/dir/abc"
        assert shorten_url(url) == "example.com/dir/abc"

        # 4 chars - should be shortened
        url = "https://example.com/dir/abcd"
        assert shorten_url(url) == "example.com/dir/abc..."

        # 2 chars - should not be shortened
        url = "https://example.com/dir/ab"
        assert shorten_url(url) == "example.com/dir/ab"
