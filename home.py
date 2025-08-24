import os
import tkinter as tk
from tkinter import ttk
import ast

# Try to use ttkbootstrap for modern theming if available
try:
	import ttkbootstrap as tb
	THEMED = True
except Exception:
	tb = None
	THEMED = False


class SafeEvaluator(ast.NodeVisitor):
	"""Safely evaluate arithmetic expressions: + - * / % ** and parentheses."""

	allowed_binops = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow)
	allowed_unary = (ast.UAdd, ast.USub)

	def visit(self, node):  # type: ignore[override]
		if isinstance(node, ast.Expression):
			return self.visit(node.body)
		if isinstance(node, ast.Num):  # Py<3.8 compatibility
			return node.n
		if isinstance(node, ast.Constant):
			if isinstance(node.value, (int, float)):
				return node.value
			raise ValueError("დაუშვებელი კონსტანტა")
		if isinstance(node, ast.BinOp) and isinstance(node.op, self.allowed_binops):
			left = self.visit(node.left)
			right = self.visit(node.right)
			return self._apply_op(node.op, left, right)
		if isinstance(node, ast.UnaryOp) and isinstance(node.op, self.allowed_unary):
			operand = self.visit(node.operand)
			if isinstance(node.op, ast.UAdd):
				return +operand
			if isinstance(node.op, ast.USub):
				return -operand
		# Disallow names, calls, attributes, etc.
		raise ValueError("დაუშვებელი გამოხატულება")

	@staticmethod
	def _apply_op(op, a, b):
		if isinstance(op, ast.Add):
			return a + b
		if isinstance(op, ast.Sub):
			return a - b
		if isinstance(op, ast.Mult):
			return a * b
		if isinstance(op, ast.Div):
			return a / b
		if isinstance(op, ast.Mod):
			return a % b
		if isinstance(op, ast.Pow):
			return a ** b
		raise ValueError("უცნობი ოპერაცია")


def safe_eval(expr: str) -> float:
	# Normalize operators commonly used in UIs
	expr = expr.replace("×", "*").replace("÷", "/").replace("^", "**")
	# Strip spaces
	expr = expr.strip()
	if not expr:
		return 0
	tree = ast.parse(expr, mode="eval")
	evaluator = SafeEvaluator()
	result = evaluator.visit(tree)
	return result


class CalculatorApp:
	def __init__(self, root: tk.Misc):
		self.root = root
		self.root.title("კალკულატორი")

		# Main container
		self.frame = ttk.Frame(root, padding=(16, 12))
		self.frame.pack(fill="both", expand=True)

		self.expr_var = tk.StringVar(value="")
		self.status_var = tk.StringVar(value="მზადაა")

		# Display entry (readonly)
		self.entry = ttk.Entry(self.frame, textvariable=self.expr_var, font=("Segoe UI", 16))
		self.entry.pack(fill="x", pady=(0, 8))
		self.entry.state(["readonly"])  # prevent direct typing into entry; we bind keys to the window

		# Status
		status_row = ttk.Frame(self.frame)
		status_row.pack(fill="x", pady=(0, 8))
		ttk.Label(status_row, text="სტატუსი:").pack(side="left")
		ttk.Label(status_row, textvariable=self.status_var).pack(side="left", padx=(6, 0))

		# Buttons grid
		grid = ttk.Frame(self.frame)
		grid.pack()

		# Layout definition
		buttons = [
			[
				{"t": "C", "style": "danger", "cmd": self.clear},
				{"t": "⌫", "style": "warning", "cmd": self.backspace},
				{"t": "(", "style": "secondary", "cmd": lambda: self.append("(")},
				{"t": ")", "style": "secondary", "cmd": lambda: self.append(")")},
			],
			[
				{"t": "7"}, {"t": "8"}, {"t": "9"}, {"t": "÷", "style": "info"},
			],
			[
				{"t": "4"}, {"t": "5"}, {"t": "6"}, {"t": "×", "style": "info"},
			],
			[
				{"t": "1"}, {"t": "2"}, {"t": "3"}, {"t": "-", "style": "info"},
			],
			[
				{"t": "0"}, {"t": "."}, {"t": "^", "style": "secondary"}, {"t": "+", "style": "info"},
			],
			[
				{"t": "%", "style": "secondary"},
				{"t": "=", "style": "primary", "span": 3, "cmd": self.equals},
			],
		]

		for r, row in enumerate(buttons):
			for c, spec in enumerate(row):
				text = spec.get("t", "")
				cmd = spec.get("cmd") or (lambda t=text: self.append(t))
				span = spec.get("span", 1)
				style = spec.get("style")
				btn = self._make_button(grid, text, style, cmd)
				btn.grid(row=r, column=c, columnspan=span, sticky="nsew", padx=4, pady=4)
			# Configure column weights for even spacing
			for c in range(4):
				grid.grid_columnconfigure(c, weight=1)

		# Keyboard bindings
		self._bind_keys()

	def _make_button(self, parent, text, style, cmd):
		if THEMED:
			# Use ttkbootstrap buttons with bootstyle when available
			bootstyle = None
			if style:
				mapping = {
					"primary": "primary",
					"secondary": "secondary",
					"info": "info",
					"warning": "warning",
					"danger": "danger",
				}
				bootstyle = mapping.get(style)
			kwargs = {"command": cmd, "text": text}
			if bootstyle:
				kwargs["bootstyle"] = bootstyle
			return tb.Button(parent, **kwargs)
		# Fallback to ttk
		return ttk.Button(parent, text=text, command=cmd)

	# Button handlers
	def append(self, s: str):
		self.status_var.set("მზადაა")
		self.expr_var.set(self.expr_var.get() + s)

	def clear(self):
		self.expr_var.set("")
		self.status_var.set("გასუფთავდა")

	def backspace(self):
		cur = self.expr_var.get()
		if cur:
			self.expr_var.set(cur[:-1])

	def equals(self):
		expr = self.expr_var.get()
		try:
			result = safe_eval(expr)
			# Normalize int-ish floats
			if isinstance(result, float) and result.is_integer():
				result = int(result)
			self.expr_var.set(str(result))
			self.status_var.set("OK")
		except ZeroDivisionError:
			self.status_var.set("განაწილება ნულზე დაუშვებელია")
		except Exception:
			self.status_var.set("შეცდომა გამოხატულებაში")

	def _bind_keys(self):
		# Digits and dot
		for ch in "0123456789.()":
			self.root.bind(ch, lambda e, t=ch: self.append(t))
		# Operators
		for ch in ["+", "-", "*", "/", "%", "^"]:
			self.root.bind(ch, lambda e, t=ch: self.append(t))
		# Enter/Eq
		self.root.bind("<Return>", lambda e: self.equals())
		self.root.bind("=", lambda e: self.equals())
		# Backspace and Escape
		self.root.bind("<BackSpace>", lambda e: self.backspace())
		self.root.bind("<Escape>", lambda e: self.clear())


def main():
	# Create window with modern theme if possible
	if THEMED:
		root = tb.Window(themename="flatly")
	else:
		root = tk.Tk()
	app = CalculatorApp(root)
	root.minsize(320, 360)
	root.mainloop()


if __name__ == "__main__":
	main()