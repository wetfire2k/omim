varying vec3 v_length;
varying vec4 v_color;

#ifdef SAMSUNG_GOOGLE_NEXUS
uniform sampler2D u_colorTex;
#endif

uniform vec4 u_color;
uniform vec4 u_outlineColor;
uniform vec4 u_routeParams;

const float kAntialiasingThreshold = 0.92;

const float kOutlineThreshold1 = 0.81;
const float kOutlineThreshold2 = 0.71;

void main(void)
{
#ifdef SAMSUNG_GOOGLE_NEXUS
  // Because of a bug in OpenGL driver on Samsung Google Nexus this workaround is here.
  const float kFakeColorScalar = 0.0;
  lowp vec4 fakeColor = texture2D(u_colorTex, vec2(0.0, 0.0)) * kFakeColorScalar;
#endif

  vec4 color = vec4(0.0, 0.0, 0.0, 0.0);
  if (v_length.x >= v_length.z)
  {
    color = mix(mix(u_color, vec4(v_color.rgb, 1.0), v_color.a), u_color, step(u_routeParams.w, 0.0));
    color = mix(color, u_outlineColor, step(kOutlineThreshold1, abs(v_length.y)));
    color = mix(color, u_outlineColor, smoothstep(kOutlineThreshold2, kOutlineThreshold1, abs(v_length.y)));
    color.a *= (1.0 - smoothstep(kAntialiasingThreshold, 1.0, abs(v_length.y)));
  }

#ifdef SAMSUNG_GOOGLE_NEXUS
  gl_FragColor = color + fakeColor;
#else
  gl_FragColor = color;
#endif
}
