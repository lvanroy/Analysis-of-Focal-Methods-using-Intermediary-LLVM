import re


# this class will be used to validate each token against the possible values a field can have
def is_linkage_type(token):
    return token in {"private", "internal", "available externally", "linkonce", "weak",
                     "common", "appending", "extern weak", "linkonce_odr", "weak_odr",
                     "external"}


def is_runtime_preemptable(token):
    return token in {"dso_preemptable", "dso_local"}


def is_visibility_style(token):
    return token in {"default", "hidden", "protected"}


def is_dll_storage_class(token):
    return token in {"dllimport", "dllexport"}


def is_calling_convention(token):
    return token in {"ccc", "fastcc", "coldcc", "cc", "cc", "webkit_jscc",
                     "anyregcc", "preserve_mostcc", "preserve_allcc", "cxx_fast_tlscc",
                     "swiftcc", "tailcc", "cfguard_checkcc"}


def is_unnamed_addr(token):
    return token in {"unnamed_addr", "local_unnamed_addr"}


def is_attribute(token):
    return is_parameter_attribute(token) | is_function_attribute(token)


def is_group_attribute(token):
    return "#" in token


def is_parameter_attribute(token):
    is_attr = token in {"zeroext", "signext", "inreg", "byval", "inalloca",
                        "sret", "noalias", "nocapture", "nofree", "nest",
                        "returned", "nonnull", "swiftself", "swifterror",
                        "immarg", "noundef", "align"}
    is_attr = is_attr or re.match(r'^byval(.*?)?', token) or re.match(r'^byref(.*?)?', token)
    is_attr = is_attr or re.match(r'^preallocated(.*?)?', token) or re.match(r'^dereferenceable(.*?)?', token)
    is_attr = is_attr or re.match(r'^align(.*?)?', token) or re.match(r'dereferenceable_or_null(.*?)?', token)
    is_attr = is_attr or re.match(r'^sret(.*)?', token)
    return is_attr


def is_function_attribute(token):
    is_attr = token in {"alwaysinline", "builtin", "cold", "convergent", "inaccessiblememonly",
                        "inaccessiblemem_or_argmemonly", "inlinehint", "jumptable", "minsize",
                        "naked", "\"no-inline-line-tables\"", "no-jump-tables", "nobuiltin",
                        "noduplicate", "nofree", "noimplicitfloat", "noinline", "nomerge",
                        "nonlazybind", "noredzone", "indirect-tls-seg-refs", "noreturn",
                        "norecurse", "willreturn", "nosync", "nounwind", "null_pointer_is_valid",
                        "optforfuzzing", "optnone", "optsize", "\"patchable-function\"",
                        "\"patchable-function\"", "readnone", "readonly", "\"stack-probe-size\"",
                        "\"no-stack-arg-probe\"", "writeonly", "argmemonly", "returns_twice",
                        "safestack", "sanitize_address", "sanitize_memory", "sanitize_thread",
                        "sanitize_hwaddress", "sanitize_memtag", "speculative_load_hardening",
                        "speculatable", "ssp", "sspreq", "sspstrong", "strictfp", "\"denormal-fp-math\"",
                        "\"denormal-fp-math-f32\"", "\"thunk\"", "uwtable", "nocf_check", "shadowcallstack",
                        "\"probe-stack\""}
    is_attr = is_attr | ("alignstack" in token) | ("allocsize" in token)
    return is_attr


def is_address_space(token):
    return "#" in token


def is_comdat(token):
    return token in {"any", "exactmatch", "largest", "noduplicates", "samesize"}


def is_metadata(token):
    return token[0] == "!"


def is_tail(token):
    return token in {"tail", "musttail", "notail"}


def is_fast_math_flag(token):
    return token in {"nnan", "ninf", "nsz", "arcp", "contract",
                     "afn", "reassoc", "fast"}


def is_tls(token):
    return token in {"localdynamic", "initialexec", "localexec"}
