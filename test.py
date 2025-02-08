def f(**args):
	print(f"a={args['a']}, b={args['b']}")

x='a=2, b=3'
args = dict(e.split('=') for e in x.split(', '))
print(args)
f(**args)