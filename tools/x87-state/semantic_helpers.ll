; Proposed static lowering only. Not applied to the native adapter yet.
; All operands are actual guest State fields or the actual loaded raw80 buffer.
; No request, case index, oracle or expected-result table is accessible.
define internal void @mw34_x87_fault_flags(ptr %state, i1 %fault, i1 %c1) alwaysinline {
entry:
  %ie = getelementptr inbounds i8, ptr %state, i32 2755
  %sf = getelementptr inbounds i8, ptr %state, i32 2757
  %c1ptr = getelementptr inbounds i8, ptr %state, i32 2739
  %old_ie = load i8, ptr %ie, align 1
  %old_sf = load i8, ptr %sf, align 1
  %faultbyte = zext i1 %fault to i8
  %c1byte = zext i1 %c1 to i8
  %new_ie = or i8 %old_ie, %faultbyte
  %new_sf = or i8 %old_sf, %faultbyte
  store i8 %new_ie, ptr %ie, align 1
  store i8 %new_sf, ptr %sf, align 1
  store i8 %c1byte, ptr %c1ptr, align 1
  ret void
}

define internal void @mw34_x87_push_prepare(ptr %state, ptr %incoming) alwaysinline {
entry:
  %swptr = getelementptr inbounds i8, ptr %state, i32 2770
  %ftwptr = getelementptr inbounds i8, ptr %state, i32 2772
  %sw = load i16, ptr %swptr, align 2
  %shifted_top = lshr i16 %sw, 11
  %destination = add i16 %shifted_top, 7
  %physical = and i16 %destination, 7
  %shift = trunc i16 %physical to i8
  %bit = shl i8 1, %shift
  %ftw = load i8, ptr %ftwptr, align 1
  %occupied = and i8 %ftw, %bit
  %overflow = icmp ne i8 %occupied, 0
  %newftw = or i8 %ftw, %bit
  store i8 %newftw, ptr %ftwptr, align 1
  call void @mw34_x87_fault_flags(ptr %state, i1 %overflow, i1 %overflow)
  %value = load i80, ptr %incoming, align 1
  %effective = select i1 %overflow, i80 1208921207928610747318272, i80 %value
  store i80 %effective, ptr %incoming, align 1
  ret void
}

define internal void @mw34_x87_pop_prepare(ptr %state) alwaysinline {
entry:
  %swptr = getelementptr inbounds i8, ptr %state, i32 2770
  %ftwptr = getelementptr inbounds i8, ptr %state, i32 2772
  %st0 = getelementptr inbounds i8, ptr %state, i32 2486
  %sw = load i16, ptr %swptr, align 2
  %shifted_top = lshr i16 %sw, 11
  %physical = and i16 %shifted_top, 7
  %shift = trunc i16 %physical to i8
  %bit = shl i8 1, %shift
  %ftw = load i8, ptr %ftwptr, align 1
  %occupied = and i8 %ftw, %bit
  %underflow = icmp eq i8 %occupied, 0
  %clearbit = xor i8 %bit, -1
  %newftw = and i8 %ftw, %clearbit
  store i8 %newftw, ptr %ftwptr, align 1
  call void @mw34_x87_fault_flags(ptr %state, i1 %underflow, i1 false)
  %value = load i80, ptr %st0, align 1
  %effective = select i1 %underflow, i80 1208921207928610747318272, i80 %value
  store i80 %effective, ptr %st0, align 1
  ret void
}

define internal void @mw34_x87_exchange_prepare(ptr %state) alwaysinline {
entry:
  %swptr = getelementptr inbounds i8, ptr %state, i32 2770
  %ftwptr = getelementptr inbounds i8, ptr %state, i32 2772
  %st0 = getelementptr inbounds i8, ptr %state, i32 2486
  %st1 = getelementptr inbounds i8, ptr %state, i32 2502
  %sw = load i16, ptr %swptr, align 2
  %shifted_top = lshr i16 %sw, 11
  %physical0 = and i16 %shifted_top, 7
  %next = add i16 %physical0, 1
  %physical1 = and i16 %next, 7
  %shift0 = trunc i16 %physical0 to i8
  %shift1 = trunc i16 %physical1 to i8
  %bit0 = shl i8 1, %shift0
  %bit1 = shl i8 1, %shift1
  %ftw = load i8, ptr %ftwptr, align 1
  %occupied0 = and i8 %ftw, %bit0
  %occupied1 = and i8 %ftw, %bit1
  %empty0 = icmp eq i8 %occupied0, 0
  %empty1 = icmp eq i8 %occupied1, 0
  %underflow = or i1 %empty0, %empty1
  %newftw0 = or i8 %ftw, %bit0
  %newftw1 = or i8 %newftw0, %bit1
  store i8 %newftw1, ptr %ftwptr, align 1
  call void @mw34_x87_fault_flags(ptr %state, i1 %underflow, i1 false)
  %value0 = load i80, ptr %st0, align 1
  %value1 = load i80, ptr %st1, align 1
  %effective0 = select i1 %empty0, i80 1208921207928610747318272, i80 %value0
  %effective1 = select i1 %empty1, i80 1208921207928610747318272, i80 %value1
  store i80 %effective0, ptr %st0, align 1
  store i80 %effective1, ptr %st1, align 1
  ret void
}

define internal void @mw34_x87_free_prepare(ptr %state) alwaysinline {
entry:
  %swptr = getelementptr inbounds i8, ptr %state, i32 2770
  %ftwptr = getelementptr inbounds i8, ptr %state, i32 2772
  %sw = load i16, ptr %swptr, align 2
  %shifted_top = lshr i16 %sw, 11
  %next = add i16 %shifted_top, 1
  %physical = and i16 %next, 7
  %shift = trunc i16 %physical to i8
  %bit = shl i8 1, %shift
  %clearbit = xor i8 %bit, -1
  %ftw = load i8, ptr %ftwptr, align 1
  %newftw = and i8 %ftw, %clearbit
  store i8 %newftw, ptr %ftwptr, align 1
  ret void
}
