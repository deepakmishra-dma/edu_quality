import {useCustomMutation} from "@refinedev/core";
import {useCallback} from "react";

interface MarkAsStaredVariables {
  notice: string
  student: string
  stared: boolean
}

const useMarkAsStared = () => {
  const {mutate, mutateAsync, ...mutationObjs} = useCustomMutation({
    mutationOptions: {}
  })
  const mutationFunction = useCallback((variables: MarkAsStaredVariables) => {
    return mutate({
      url: '/api/method/edu_quality.public.py.walsh.notices.mark_as_stared',
      method: 'post',
      values: variables
    })
  }, [mutate])
  const mutationAsyncFunction = useCallback((variables: MarkAsStaredVariables) => {
    return mutateAsync({
      url: '/api/method/edu_quality.public.py.walsh.notices.mark_as_stared',
      method: 'post',
      values: variables
    })
  }, [mutateAsync])
  return {
    ...mutationObjs,
    mutate: mutationFunction,
    mutateAsync: mutationAsyncFunction
  }
}

export default useMarkAsStared
