uWu_nyaa() => {
    n wa 0

    daijoubu(n <= 100) {
        yomu(n)
        n++

        nani(n == 100) {
            daijoubu(n >= 0) {
                yomu(n)
                n--
            }
        }

        nani (n == -1) { yamete }
    }
}