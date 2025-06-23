template = """
<code>Code Snippet</code>
<flip>Flipped Text</flip>
<right><flip>Flipped Text aligned</flip></right>
<invert>Inverted Text</invert>
<u1>Underlined Text</u1>
<u2>Bolder Underlined Text</u2>
<b>Bold Text</b>
<u2><b>Boldest Underlined Text</b></u2>
Normal Text
<h1>Header 1</h1>
<h2>Header 2</h2>
<center>Centered Text</center>
<h2><invert>Inverted Header</invert></h2>

image if any:
{image}
message if any:
{text}
qr_codes if any:
{qr_codes}

From: {sender}
Sent at: {sent}
Received at: {received}
Printed at: {printed}
"""