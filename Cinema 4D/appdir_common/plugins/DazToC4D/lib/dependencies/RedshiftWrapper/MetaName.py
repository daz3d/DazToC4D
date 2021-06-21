"""
MIT License

Copyright (c) 2017 Gr4ph0s

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import c4d


class MetaMat(object):
    NodeColor = c4d.Vector(0.8, 0.4, 0.4)

    # Materials
    MatArchi = "Architectural"
    MarCar = "CarPaint"
    MatHair = "Hair"
    MatIncande = "Incandescent"
    MatDefault = "Material"
    MatBlender = "MaterialBlender"
    MatShadow = "MatteShadow"
    MatSkin = "Skin"
    MatSprite = "Sprite"
    MatSSS = "SubSurfaceScatter"


class MetaTex(object):
    NodeColor = c4d.Vector(0.98, 0.635, 0.008)

    # Textures
    TexAO = "AmbientOcclusion"
    TexCamMap = "CameraMap"
    TexCurvature = "Curvature"
    TexNoise = "RSNoise"
    TexRamp = "RSRamp"
    TexSampler = "TextureSampler"
    TexWire = "WireFrame"


class MetaUtils(object):
    NodeColor = c4d.Vector(0.349, 0.514, 1)

    # utility
    UtBumpBlend = "BumpBlender"
    UtBump = "BumpMap"
    UtHairAttr = "C4DHairAttribute"
    UtBaker = "C4DBaker"
    UtUDColor = "RSUserDataColor"
    UtConstant = "400001120"
    UtDisplace = "Displacement"
    UtDisplaceBlend = "DisplacementBlender"
    UtFresnel = "Fresnel"
    UtHairPos = "RSHairPosition"
    UtHairRandom = "HairRandomColor"
    UtUDInt = "RSUserDataInteger"
    UtNormap = "NormalMap"
    UtParticleAttr = "ParticleAttributeLookup"
    UtRaySwitch = "RaySwitch"
    UtRoundCorners = "RoundCorners"
    UtUDScalar = "RSUserDataScalar"
    UtShaderSwitch = "RSShaderSwitch"
    UtState = "State"
    UtTriPlanar = "TriPlanar"
    UtUDVector = "RSUserDataVector"
    UtVertexAttr = "VertexAttributeLookup"


class MetaEnv(object):
    NodeColor = c4d.Vector(0.537, 0.443, 0.984)

    # Environment
    Env = "Environment"
    EnvSky = "PhysicalSky"


class MetaLight(object):
    NodeColor = c4d.Vector(0.8, 0.8, 0.8)

    # Light
    LightDome = "Light_Dome"
    LightIes = "Light_IES"
    Light = "Light"
    LightPortal = "Light_Portal"
    LightSun = "PhysicalSun"


class MetaVolume(object):
    NodeColor = c4d.Vector(0.361, 0.8, 0.8)

    # Volume
    Volume = "Volume"


class MetaMath(object):
    NodeColor = c4d.Vector(0.333, 1, 0.635)

    # Math
    MathAbs = "RSMathAbs"
    MathAdd = "RSMathAdd"
    MathACos = "RSMathACos"
    MathASin = "RSMathASin"
    MathATan2 = "RSMathATan2"
    MathATan = "RSMathATan"
    MathBias = "RSMathBias"
    MathRange = "RSMathRange"
    MathCos = "RSMathCos"
    MathCrossVector = "RSMathCrossVector"
    MathDiv = "RSMathDiv"
    MathDotVector = "RSMathDotVector"
    MathExp = "RSMathExp"
    MathFloor = "RSMathFloor"
    MathFrac = "RSMathFrac"
    MathGain = "RSMathGain"
    MathInv = "RSMathInv"
    MathLn = "RSMathLn"
    MathLog = "RSMathLog"
    MathMax = "RSMathMax"
    MathMin = "RSMathMin"
    MathMix = "RSMathMix"
    MathMod = "RSMathMod"
    MathMul = "RSMathMul"
    MathNeg = "RSMathNeg"
    MathNormalizeVector = "RSMathNormalizeVector"
    MathPow = "RSMathPow"
    MathRcp = "RSMathRcp"
    MathSaturate = "RSMathSaturate"
    MathSign = "RSMathSign"
    MathSin = "RSMathSin"
    MathSqrt = "RSMathSqrt"
    MathSub = "RSMathSub"
    MathTan = "RSMathTan"
    MathAbsVector = "RSMathAbsVector"
    MathAddVector = "RSMathAddVector"
    MathBiasVector = "RSMathBiasVector"
    MathRangeVector = "RSMathRangeVector"
    MathDivVector = "RSMathDivVector"
    MathExpVector = "RSMathExpVector"
    MathFloorVector = "RSMathFloorVector"
    MathFracVector = "RSMathFracVector"
    MathGainVector = "RSMathGainVector"
    MathInvVector = "RSMathInvVector"
    MathLengthVector = "RSMathLengthVector"
    MathLnVector = "RSMathLnVector"
    MathLogVector = "RSMathLogVector"
    MathMaxVector = "RSMathMaxVector"
    MathMinVector = "RSMathMinVector"
    MathMixVector = "RSMathMixVector"
    MathModVector = "RSMathModVector"
    MathMulVector = "RSMathMulVector"
    MathNegVector = "RSMathNegVector"
    MathPowVector = "RSMathPowVector"
    MathRcpVector = "RSMathRcpVector"
    MathSaturateVector = "RSMathSaturateVector"
    MathSignVector = "RSMathSignVector"
    MathSqrtVector = "RSMathSqrtVector"
    MathSubVector = "RSMathSubVector"
    MathRSVectorToScalars = "RSVectorToScalars"


class MetaColor(object):
    NodeColor = c4d.Vector(0.094, 0.776, 0.278)

    # Color
    ColorAbsColor = "RSMathAbsColor"
    ColorRange = "RSColorRange"
    ColorComposite = "RSColorComposite"
    ColorCorrection = "RSColorCorrection"
    ColorExpColor = "RSMathExpColor"
    ColorGainColor = "RSMathGainColor"
    ColorInvColor = "RSMathInvColor"
    ColorLayer = "RSColorLayer"
    ColorMaker = "RSColorMaker"
    ColorMix = "RSColorMix"
    ColorSaturateColor = "RSMathSaturateColor"
    ColorSplitter = "RSColorSplitter"
    ColorSubColor = "RSMathSubColor"
    Color2HSV = "RSColor2HSV"
    ColorRSHSV2Color = "RSHSV2Color"
    ColorBiasColor = "RSMathBiasColor"


class MetaOut(object):
    NodeColor = c4d.Vector(0.204, 0.443, 0.682)

    # Output
    Output = "Output"


class MetaName(
    MetaMat,
    MetaTex,
    MetaUtils,
    MetaEnv,
    MetaLight,
    MetaVolume,
    MetaMath,
    MetaColor,
    MetaOut,
):
    """Class for storing all possibles metaname."""

    def _TestProperty(self, valueToTest, classToTest=None):
        """Test if any properties of :class:`MetaclassName` have a specific value, This fonction is used to test if a string is under MetaName.

        :param valueToTest: value to test if it's inside MetaName.
        :type valueToTest: str
        :param classToTest: class to test if valueToTest is within.
        :type classToTest: class
        :return: True if it's on MetaName overtwise False.
        :rtype: Bool
        """
        obj = None
        if classToTest is None:
            obj = MetaName()
        else:
            obj = classToTest
        for attr in dir(obj):
            if getattr(type(obj), attr, None) == valueToTest:
                return True

        return False

    def GetDefaultColorNode(self, nodeType):
        """Get the Default color for a node given it's type.

        :param nodeType: The MetaName type to test.
        :type nodeType: str
        :return: Default color.
        :rtype: c4d.Vector
        """
        classToTest = list()
        classToTest.append(MetaMat())
        classToTest.append(MetaTex())
        classToTest.append(MetaUtils())
        classToTest.append(MetaEnv())
        classToTest.append(MetaLight())
        classToTest.append(MetaVolume())
        classToTest.append(MetaMath())
        classToTest.append(MetaColor())
        classToTest.append(MetaOut())

        color = c4d.Vector(0.38, 0.384, 0.392)

        for cls in classToTest:
            if self._TestProperty(nodeType, cls):
                color = cls.NodeColor
        return color
