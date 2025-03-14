# RhinoMCP Prompt Engineering Guide

This document provides guidance on effective prompt templates and strategies when using Claude AI with RhinoMCP for 3D modeling tasks.

## Overview

RhinoMCP exposes Rhino3D functionality to Claude through the Model Context Protocol, allowing the AI to create and manipulate 3D geometry. Effective prompts help Claude understand the design intent and execute the appropriate commands.

## Prompt Templates

### Basic Curve Creation

```
Create a NURBS curve in Rhino with the following points:
- Point 1: (0, 0, 0)
- Point 2: (5, 10, 0)
- Point 3: (10, 0, 0)
- Point 4: (15, 5, 0)
```

### Running Python Script in Rhino

```
Execute the following Python script in Rhino to [describe purpose]:

```python
# Your Python code here
import Rhino
import rhinoscriptsyntax as rs

# Example: Create a sphere
rs.AddSphere([0,0,0], 5)
```
```

### Checking Rhino Status

```
Check if Rhino is connected and report back with the version information.
```

## Prompt Strategies

### Be Specific with Coordinates

When creating geometry, provide exact coordinates rather than descriptive positions. This reduces ambiguity and ensures precise results.

**Good:**
```
Create a curve from (0,0,0) to (10,10,0) to (20,0,0)
```

**Less Effective:**
```
Create a curve that starts at the origin, goes up and to the right, then back down
```

### Use Visual References

For complex shapes, provide a visual reference or description to help Claude understand the desired outcome.

```
Create a curve that forms an "S" shape in the XY plane, starting at (0,0,0) 
and ending at (20,0,0), with control points approximately at:
- (0,0,0)
- (5,10,0)
- (15,-10,0)
- (20,0,0)
```

### Iterate and Refine

Start with simple commands and gradually refine the design through conversation.

```
Step 1: Create a basic curve along the X-axis from (0,0,0) to (20,0,0)
Step 2: Now modify that curve to have a height of 5 units at its midpoint
Step 3: Create a second curve parallel to the first, offset by 10 units in the Y direction
```

### Specify Units

Always specify units when relevant to ensure the correct scale.

```
Create a sphere with radius 5 millimeters at position (10,10,10)
```

## Common Patterns

### Design Iteration

```
1. Create a basic version of [design element]
2. Evaluate the result
3. Modify specific aspects: "Make this part more [attribute]"
4. Continue refining until satisfied
```

### Reference-Based Design

```
1. Begin with a reference: "Create a curve similar to [description]"
2. Provide feedback on how to adjust
3. Add features or modify to match requirements
```

## Input Constraints

- Coordinate values should be numeric (avoid descriptive terms like "a little to the left")
- Python scripts must be compatible with Rhino's Python environment
- Avoid requesting operations on nonexistent objects

## Examples of Effective Prompts

### Example 1: Simple Curve

```
Create a NURBS curve in Rhino that forms a simple arc in the XY plane. 
Use these points:
- (0,0,0)
- (5,5,0)
- (10,0,0)
```

### Example 2: Script-Based Operation

```
I want to create a grid of spheres in Rhino. Please execute a Python script that:
1. Creates a 3x3 grid of spheres
2. Sets the grid spacing to 10 units
3. Makes each sphere have a radius of 2 units
```

### Example 3: Multiple Operations

```
Let's create a simple model of a wine glass:
1. First create a vertical curve for the profile
2. Then create a circle at the base for the foot
3. Finally, use the existing Rhino commands to revolve the profile curve around the vertical axis
```
