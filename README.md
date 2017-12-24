ping-analyzer

Design and implementation notes are in:
"Marc Donner Engineering Notebook," a private Google document 

2017-12-23

What is ping-analyzer all about?

A habit that I have developed over the course of many years of using
the Internet is to keep a ping running in a terminal session.  It
provides me with a simple view of my connection to the Internet.
If my ping shows a problem with connectivity from my desktop to
some important server outside, say google.com, then I can expect
problems with many of my Internet-based activities.

[What is ping?  Ping is a program that uses the ICMP ECHO service
defined in RFC 792 to repeatedly send messages to a remote system
and report back on the success or failure to receive a returned
message and, in the case of success, the round trip time.  Ping was
written in the early 1980s by the late Mike Muuss at the Ballistic
Research Laboratory.]

As the Internet has become increasingly commercialized I have had
to learn to deal with ISPs with varying levels of technical skill.
Typically, the technical support lines at commercial ISPs are usually
populated by nontechnical people who are provided with weak diagnostic
tools, little understanding of the architecture of networks, and
no authority to go beyond a very limited set of responses.  And the
set of complaints that they are prepared to handle typically do not
include subtle failures like intermittent but regulard connectivity
loss, routing failures, DNS problems, or other technical errors.

Architectural view and implied requirements

My home network is reasonably complex and I presume that it is
similar to that of other technical folks.  In particular, it has
an internal firewall / router connected to a terminal adapter
provided by the ISP.  In order to keep an eye on the health of
my connectivity I need to ping several addresses all at once:

1 - the external site that is my canary

2 - the internal address of my ISP's terminal adapter

3 - the internal address of my firewall / router

So my design needs to support several things:

a - multiple concurrent ping streams

b - time synchronization.  This supports two needs:
      (1) ability to document to an ISP the date and time
          of an outage, and
      (2) the ability to correlate multiple streams of pings.

c - logging of the ping streams for subsequent analysis
