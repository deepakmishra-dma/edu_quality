let intervalRef = null


window.addEventListener('load', () => {
    (function () {
        //    window.nativeInterface.logToNative('ssss')
        if (!window.nativeInterface) return

        // nativeInterface.logToNative('hiya from other side')
        try {
            if (intervalRef)
                clearInterval(intervalRef)
            function runBackgroundCarnivalJob() {
                nativeInterface.execute('backgroundFileJob').then((data) => {
                    nativeInterface.logToNative(data)
                })
            }
            runBackgroundCarnivalJob()
            intervalRef = setInterval(() => {

                try {
                    // frappe.msgprint({
                    //     title: __('Successful'),
                    //     message: __(';x'),

                    // })
                    runBackgroundCarnivalJob()
                } catch (e) {
                    // frappe.msgprint({
                    //     title: __('Successful'),
                    //     message: __(e.message),

                    // })
                }
            }, 30000)
        }
        catch (e) {
            frappe.msgprint({
                title: __('Successful'),
                message: __(e.message),

            })
        }
    })()
})
