#!/usr/bin/perl
#
#  History:
#
#    [2001-02-17, 00:41-02:03] v1.0a - experimental (still learning Perl)
#    [2001-02-18,~01:30-02:15] v1.0b - experimental (still learning Perl)
#    [2001-02-23, 07:29-08:28] v1.0 - working version.
#    [2001-11-01,~23:00-01:28] v2.0 - primitive web interface.
#    [2010-09-15, 17:10-]
#    [2010-11-22, 22:15-22:48] v2.1
#    [2010-11-22, 01:08-02:37] v2.1 - now uses HTML5 autodocus & placeholder
#    text features; solved the pesky UTF8-when-reading-and-url-decoding-input-
#    in-enviroment-variables problem
#    [2013-10-08, 03:48-03:50] v2.2 - updated by name
#
#
#  To Do:
#
#    o This thing still is not compatible with my ARexx program,
#      since it won't automatically strip spaces etc. from the
#      word given on the command line.
#

use strict;
use warnings;
use utf8;                                # source is UTF8
binmode(STDOUT, ":utf8");                # STDOUT is UTF8
use open IN => ":encoding(iso-8859-1)";  # input files are LATIN1

# decodes a url with %HX and +=space notation
sub url_decode(;@) {
    use bytes;
    my @string = (@_ ? @_ : $_);               # get args or $_
    foreach (@string) {                        # for each scalar
        next unless defined;                   #   skip undefined values
        s/\+/ /g;                              #   turn plus into space
        s/%([0-9a-f]{2})/                      #   turn all %HX into
            chr(hex $1);                       #     normal characters
        /ogei;                                 #
    }                                          #
    return @string == 1 ? $string[0] : @string;  # return string (if one only
}                                              #   one arg was given) or array

sub empty_form_text {
    return <<"EOF";

<div style="max-width: 30em;">

<p>Welcome to my English–Swedish/Swedish–English dictionary.&nbsp;
It&rsquo;s not perfect, but decent enough that I have bothered to do a minor update
of this script to bring it into the 21st century.&nbsp; Do a couple of
searches, and see how you like it!</p>

<p>You may use an asterisk (<code>*</code>) to match anything in your searches,
e.g. you could use »<code>hej*</code>« to search for all words beginning with
<em>hej</em>.&nbsp; A single asterisk is not a valid search, however.</p>

</div>
EOF
}


print "Content-type: text/html\n\n";           # http-header

use Encode;
my $query = exists($ENV{QUERY_STRING}) ? Encode::decode('utf8', $ENV{QUERY_STRING}) : "";

# print "<table>\n";
# foreach (sort keys %ENV) {
#     print "<tr><td>".Encode::decode('utf8', $_)."<td>".Encode::decode('utf8', $ENV{$_})."</tr>\n";
# }
# print "</table>\n";

my %q = ();                                    # init query hash
foreach (split /&/, $query) {                  # for each value in query
    my ($key, $value) = split(/=/, $_, 2);     #   split into key/value pair
    $q{url_decode($key)} = url_decode($value)  #   store in query hash
}                                              #

my $dict = defined($q{l}) ? $q{l} : "";
my $word = defined($q{w}) ? $q{w} : "";

my %lang_option = (
    en => "English–Swedish",
    sv => "Swedish–English",
);

print <<"EOF";
<!DOCTYPE html>
<html lang=en>
<head>
  <title>Swedish/English Dictionary (by Zrajm)</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <meta name="geo.region" content="SE-C">
  <meta name="geo.placename" content="Europe, Sweden, Uppsala, Kåbo">
  <meta name="geo.position" content="59.845658;17.630797">
  <link type="image/png" rel=icon href="/pic/favicon.png">
</head>
<body vlink="#777777" alink="#aaaaaa" link="#444444" text="#000000" bgcolor="#ffffff">

<a href="..">Back to zrajm's web page</a>

<h1>English/Swedish Dictionary</h1>
<form action="." method=get accept-charset="UTF-8">
  <select name=l>
EOF
foreach (sort keys %lang_option) {
    print "    <option value=\"$_\"" .
        (m/^$q{l}$/ ? ' selected=selected' : '') .
        ">$lang_option{$_}</option>\n";
}
print <<"EOF";
  </select
  ><input size=40 name=w value="$word" placeholder="Enter a word" autofocus
  ><input type=submit value=Search>
</form>
EOF


# if there was a search query -- present result
QUERY: {
    if (not $query) {
        print empty_form_text();
        last QUERY;
    }

    my $file = "";
    if ($dict eq "sv") {                           # what dictionary to use?
	$file = "data/sveeng";                     # Swedish--English
	print "<h2>Searched for »$word« in the Swedish–English Dictionary</h2>";
    } else {                                       #
	$file = "data/engsve";                     # English--Swedish
	print "<h2>Searched for »$word« in the English–Swedish Dictionary</h2>";
    }

    $word = quotemeta($word);
    $word = '\{' . $word . '\}';                   # make regexp
    $word =~ s/(\\[-­*])+/.\*/g;                   # replace - with .*

    if ($word eq '\{.*\}') {
	print "<p>Can&rsquo;t search for <i>everything</i>.&nbsp;";
	print "You need to limit yourself to a proper search word.</p>";
        last QUERY;
    }

    ## search and output result
    open(my $indexfh, "<", "$file.idx") or             # open index file
	die "$0: failed to open index file '$file.idx': $!";
    open(my $dictfh, "<", "$file.txt") or              # open dictionary
	die "$0: failed to open dictionary file '$file.txt': $!";
    my $found_count = 0;
    while (<$indexfh>) {                           # go thru index
	next unless /$word/;
        $found_count ++;
	my ($offset) = split(/:/);                 #   get offset of word
	seek($dictfh, $offset, 0);                 #   go to word in dictionary
	$_ = <$dictfh>;                            #   read first row
	s/^\{(.*)\}$/$1/;                          #   remove "{" and "}"
	print "<p><b>$_</b>";                      #   output lookup word
	while ("\n" ne ($_ = <$dictfh>)) {         #   read until blank row
	    s/\t/     /g;                          #   tabs = spaces
	    print "<br>$_";                        #   output
	}                                          #
    }                                              #
    close($dictfh);                                # close dictionary
    close($indexfh);                               # close index file
    print "\n<p>Nothing found</p>\n"
        if $found_count == 0;
}

print <<"EOF";

<div class=footer align=center>
<table class=footer bgcolor="#cccccc" border=0 width="100%">
<tr><td>Written by <a href="http://zrajm.org/">zrajm</a>, 2001–2010.&nbsp;
All copying is strictly permitted.
</table>
</div>

<!-- start-of-google-analytics -->
<script type="text/javascript">
var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
</script>
<script type="text/javascript">
var pageTracker = _gat._getTracker("UA-5434527-1");
pageTracker._trackPageview();
</script>
<!-- end-of-google-analytics -->
</body>
</html>
EOF

__END__
