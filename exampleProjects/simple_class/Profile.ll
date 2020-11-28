; ModuleID = './source/Profile.cpp'
source_filename = "./source/Profile.cpp"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

%class.Profile = type { %"class.std::__1::basic_string", %"class.std::__1::basic_string" }
%"class.std::__1::basic_string" = type { %"class.std::__1::__compressed_pair" }
%"class.std::__1::__compressed_pair" = type { %"struct.std::__1::__compressed_pair_elem" }
%"struct.std::__1::__compressed_pair_elem" = type { %"struct.std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char> >::__rep" }
%"struct.std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char> >::__rep" = type { %union.anon }
%union.anon = type { %"struct.std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char> >::__long" }
%"struct.std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char> >::__long" = type { i64, i64, i8* }

; Function Attrs: noinline optnone uwtable
define dso_local void @_ZN7Profile12setFirstNameENSt3__112basic_stringIcNS0_11char_traitsIcEENS0_9allocatorIcEEEE(%class.Profile* %0, %"class.std::__1::basic_string"* %1) #0 align 2 {
  %3 = alloca %class.Profile*, align 8
  store %class.Profile* %0, %class.Profile** %3, align 8
  %4 = load %class.Profile*, %class.Profile** %3, align 8
  %5 = getelementptr inbounds %class.Profile, %class.Profile* %4, i32 0, i32 0
  %6 = call dereferenceable(24) %"class.std::__1::basic_string"* @_ZNSt3__112basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEEaSERKS5_(%"class.std::__1::basic_string"* %5, %"class.std::__1::basic_string"* dereferenceable(24) %1)
  ret void
}

declare dso_local dereferenceable(24) %"class.std::__1::basic_string"* @_ZNSt3__112basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEEaSERKS5_(%"class.std::__1::basic_string"*, %"class.std::__1::basic_string"* dereferenceable(24)) #1

; Function Attrs: noinline optnone uwtable
define dso_local void @_ZN7Profile12getFirstNameEv(%"class.std::__1::basic_string"* noalias sret %0, %class.Profile* %1) #0 align 2 {
  %3 = alloca i8*, align 8
  %4 = alloca %class.Profile*, align 8
  %5 = bitcast %"class.std::__1::basic_string"* %0 to i8*
  store i8* %5, i8** %3, align 8
  store %class.Profile* %1, %class.Profile** %4, align 8
  %6 = load %class.Profile*, %class.Profile** %4, align 8
  %7 = getelementptr inbounds %class.Profile, %class.Profile* %6, i32 0, i32 0
  call void @_ZNSt3__112basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEEC1ERKS5_(%"class.std::__1::basic_string"* %0, %"class.std::__1::basic_string"* dereferenceable(24) %7)
  ret void
}

declare dso_local void @_ZNSt3__112basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEEC1ERKS5_(%"class.std::__1::basic_string"*, %"class.std::__1::basic_string"* dereferenceable(24)) unnamed_addr #1

attributes #0 = { noinline optnone uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "frame-pointer"="all" "less-precise-fpmad"="false" "min-legal-vector-width"="0" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "frame-pointer"="all" "less-precise-fpmad"="false" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{!"clang version 10.0.0-4ubuntu1 "}
