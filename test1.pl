#!/usr/bin/perl
package MyParser;
use base qw(HTML::Parser);

our ($text_elements, $start_tags, $end_tags);

sub text	{ $text_elements++	}
sub start	{ $start_tags++		}
sub end		{ $end_tags++		}

package main;
my $parser = MyParser->new;
$parser->parse_file("test.hocr");

print "text elements: ", $MyParser::text_elements,	"\n";
print "start tags: ", $MyParser::start_tags,		"\n";
print "end tags: ", $MyParser::end_tags,		"\n";